import os
import json
import re
import time
import argparse
import pandas as pd
from collections import defaultdict
from copy import deepcopy
from easydict import EasyDict
from tqdm import tqdm

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import FewShotChatMessagePromptTemplate, ChatPromptTemplate

from prompts import (
    EMPTY_TABLE_GEN_PROMPT,
    ENTITY_OPERATION_EXTRACTION_SYSTEM_ROBUST_PROMPT,
    ANSWER_GEN_W_OPERATION_SYSTEM_PROMPT,
    TABLE_FILLING_PROMPT,
)
from shot_examples import six_shot_robust_examples


def parse_columns(empty_table_content):
    """
    Parse column names from generated empty table markdown string.
    """
    table_prompt_part_match_pattern = r"```(.*?)```"
    table_prompt_part_match = re.search(table_prompt_part_match_pattern, empty_table_content, re.DOTALL)
    table_markdown_part_match_pattern = r"\|.*\|"

    if table_prompt_part_match:
        table_part_string = table_prompt_part_match.group(1)
        split_by_lines = table_part_string.split("\n")
        if "|" in split_by_lines[0]:
            splited_columns = split_by_lines[0].split("|")
        else:
            splited_columns = split_by_lines[1].split("|")
        columns = [x.strip() for x in splited_columns if len(x) > 1]
        return columns
    elif re.search(table_markdown_part_match_pattern, empty_table_content):
        matches = re.findall(table_markdown_part_match_pattern, empty_table_content)
        for match in matches:
            if re.search(r"\w", match):
                splited_columns = match.split("|")
                columns = [x.strip() for x in splited_columns if len(x) > 1]
                return columns
    else:
        print(f"Can't find table parts in the string. Given string: {empty_table_content}")
        return []

    return []


def filter_table_by_columns(entities, table_dicts):
    """
    Filter given table dictionaries based on extracted entities (Table_name.Column_name).
    """
    entities_list = entities.split(",")
    relevant_tables = defaultdict(dict)
    columns_by_table_name = defaultdict(list)

    for entity in entities_list:
        entity = entity.strip()
        splited_entities = entity.split(".")
        if len(splited_entities) == 2:
            table_name, column_name = splited_entities
        elif len(splited_entities) > 2:
            table_name = splited_entities[0]
            column_name = ".".join(splited_entities[1:])
        else:
            continue
        columns_by_table_name[table_name.strip()].append(column_name.strip())

    for table_name, relevant_columns in columns_by_table_name.items():
        table_pd = None
        target_table_name = table_name

        if target_table_name in table_dicts:
            t_info = table_dicts[target_table_name]
            table_pd = pd.DataFrame(columns=t_info["columns"], index=t_info.get("index", range(len(t_info["data"]))), data=t_info["data"])
        elif len(table_dicts) == 1:
            target_table_name = list(table_dicts.keys())[0]
            t_info = table_dicts[target_table_name]
            table_pd = pd.DataFrame(columns=t_info["columns"], index=t_info.get("index", range(len(t_info["data"]))), data=t_info["data"])
        else:
            for org_name in table_dicts:
                if re.search(re.escape(table_name), org_name, re.IGNORECASE) or re.search(re.escape(org_name), table_name, re.IGNORECASE):
                    target_table_name = org_name
                    t_info = table_dicts[target_table_name]
                    table_pd = pd.DataFrame(columns=t_info["columns"], index=t_info.get("index", range(len(t_info["data"]))), data=t_info["data"])
                    break

        if table_pd is None:
            continue

        # Column filtering with fallback matching
        matched_columns = [col for col in relevant_columns if col in table_pd.columns]
        if not matched_columns:
            # Greedy matching
            for rel_col in relevant_columns:
                for raw_col in table_pd.columns:
                    if str(raw_col).lower() in str(rel_col).lower() or str(rel_col).lower() in str(raw_col).lower():
                        if raw_col not in matched_columns:
                            matched_columns.append(raw_col)

        if matched_columns:
            relevant_tables[target_table_name] = table_pd.loc[:, matched_columns].to_dict(orient="split")
        else:
            relevant_tables[target_table_name] = table_pd.to_dict(orient="split")

    return dict(relevant_tables)


def prepare_normal_inputs(dataset):
    """
    Format normal dataset inputs (questions and table dicts).
    """
    questions = [data["question"] for data in dataset]
    table_dict_list = []

    for data in dataset:
        tables = data["tables"]
        table_names = data["table_names"]
        temp = defaultdict(dict)
        table_name_counts = defaultdict(lambda: 0)

        for table_name, table_data in zip(table_names, tables):
            table_name_counts[table_name] += 1
            table_json = json.loads(table_data) if isinstance(table_data, str) else table_data
            if table_name in temp:
                dedup_name = f"{table_name}_#{table_name_counts[table_name]}"
                temp[dedup_name] = table_json
            else:
                temp[table_name] = table_json
        table_dict_list.append(dict(temp))

    return questions, table_dict_list


def prepare_noisy_inputs(dataset):
    """
    Format noisy dataset inputs with injected noise tables.
    """
    questions = [data["question"] for data in dataset]
    table_dict_list = []

    for data in dataset:
        tables = data.get("tables", [])
        table_names = data.get("table_names", [])
        noise_tables = data.get("noise_tables", [])
        noise_table_names = data.get("noise_table_names", [])

        table_name_counts = defaultdict(lambda: 0)
        temp = defaultdict(dict)

        for table_name, table_data in zip(table_names, tables):
            table_json = json.loads(table_data) if isinstance(table_data, str) else table_data
            table_name_counts[table_name] += 1
            temp[table_name] = table_json

        for table_name, table_data in zip(noise_table_names, noise_tables):
            table_json = json.loads(table_data) if isinstance(table_data, str) else table_data
            table_name_counts[table_name] += 1
            if table_name in temp:
                dedup_name = f"{table_name}_#{table_name_counts[table_name]}"
                temp[dedup_name] = table_json
            else:
                temp[table_name] = table_json

        table_dict_list.append(dict(temp))

    return questions, table_dict_list


def create_entity_extraction_prompt(batch_questions, batch_table_dicts):
    """
    Create prompts for Entity & Operation extraction step.
    """
    base_prompt = "Question: {question}"
    table_schema_placeholder = "Example Tables: \n<table_name> : {table_name} col: {table_col} "

    entity_extraction_prompts = []
    for question, table_dict in zip(batch_questions, batch_table_dicts):
        prompt = base_prompt.format(question=question)
        for table_name, table_info in table_dict.items():
            columns = table_info["columns"]
            markdown_columns = " | ".join(str(c) for c in columns)
            prompt += table_schema_placeholder.format(table_name=table_name, table_col=markdown_columns)
            str_rows = [[str(y) for y in row] for row in table_info.get("data", [])]
            joined_rows = [f"row {idx+1} : {' | '.join(row)}" for idx, row in enumerate(str_rows)]
            prompt += " " + " ".join(joined_rows[:3])
        entity_extraction_prompts.append(prompt)
    return entity_extraction_prompts


def create_table_filling_prompt(entities, table_dicts, empty_table_column):
    """
    Create prompt for Table Filling step with filtered source tables.
    """
    filtered_tables = filter_table_by_columns(entities, table_dicts)
    return TABLE_FILLING_PROMPT.format(tables=filtered_tables, empty_table=empty_table_column)


def create_answer_gen_prompt(table_filling_content, question, operations):
    """
    Create prompt for final Answer Generation step.
    """
    table_match_pattern = r"```(.*?)```"
    table_match = re.search(table_match_pattern, table_filling_content, re.DOTALL)
    if table_match:
        sub_table = table_match.group(1)
    else:
        sub_table = "|".join(table_filling_content.split("|")[1:])

    ops_list = [op.strip() for op in operations.split(",") if op.strip()]
    return f"Table Data: {sub_table}\nQuestion: {question}\nOperations: {ops_list}"


def handle_rate_limit(chat, batch_input):
    """
    Execute batch LLM requests with exponential backoff on failure.
    """
    while True:
        try:
            return chat.batch(batch_input)
        except Exception as e:
            print(f"Rate limit / API error encountered: {e}. Retrying in 15 seconds...")
            time.sleep(15)


def postprocess_entity_operation_extraction(entity_extraction_contents):
    """
    Extract operations and entities from the LLM extraction output.
    """
    operations = []
    entities = []

    op_match_pattern = r"\*\*Operations\*\*:(.*?)(?=\*\*Extracted Entities\*\*)"
    op_part_match_pattern = r"\#o\d\:(.*)"
    entity_match_pattern = r"\*\*Extracted Entities\*\*:(.*)"
    entity_part_match_pattern = r"\#e\d\:(.*)"

    for content in entity_extraction_contents:
        operations_temp = []
        entities_temp = []
        operation_matches = re.findall(op_match_pattern, content, re.DOTALL)
        entity_matches = re.findall(entity_match_pattern, content, re.DOTALL)

        if operation_matches:
            for operation_match in operation_matches:
                for operation_part in operation_match.strip().split("\n"):
                    op_part_match = re.search(op_part_match_pattern, operation_part)
                    if op_part_match:
                        op_str = op_part_match.group(1).strip().rstrip(",").rstrip(".")
                        operations_temp.append(op_str)
            if not operations_temp:
                operations_temp.append("select")
        else:
            operations_temp.append("select")

        if entity_matches:
            for entity_match in entity_matches:
                for entity_part in entity_match.strip().split("\n"):
                    entity_part_match = re.search(entity_part_match_pattern, entity_part)
                    if entity_part_match:
                        e_str = entity_part_match.group(1).strip().rstrip(",").rstrip(".")
                        entities_temp.append(e_str)
            if not entities_temp:
                entities_temp.append("Entity extraction failure")
        else:
            entities_temp.append("Entity extraction failure")

        operations.append(",".join(operations_temp))
        entities.append(",".join(entities_temp))

    return entities, operations


class EASE:
    def __init__(self, args, data):
        self.args = args

        # Initialize Chat Model (OpenAI or Anthropic)
        model_name = args.get("openai_model") or args.get("anthropic_model") or args.get("model_name", "gpt-4o")
        is_claude = "claude" in model_name.lower() or args.get("model_provider") == "anthropic"

        if is_claude:
            api_key = args.get("anthropic_api_key") or os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("Anthropic API Key is missing. Please set it in config or export ANTHROPIC_API_KEY.")
            self.chat_model = ChatAnthropic(
                api_key=api_key,
                model=model_name,
                temperature=args.get("temperature", 0),
                max_tokens=args.get("max_tokens", 16383),
            )
        else:
            api_key = args.get("openai_api_key") or os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API Key is missing. Please set it in config or export OPENAI_API_KEY.")
            self.chat_model = ChatOpenAI(
                openai_api_key=api_key,
                model=model_name,
                temperature=args.get("temperature", 0),
                max_tokens=args.get("max_tokens", 16383),
                model_kwargs={"seed": args.get("seed", 144)},
            )

        # Prepare Inputs
        if "noisy_table" in self.args.get("data_setting", "noisy_table"):
            self.questions, self.tables = prepare_noisy_inputs(data)
        else:
            self.questions, self.tables = prepare_normal_inputs(data)

        # Prompts & Chains
        self.base_chat_prompt = ChatPromptTemplate.from_messages([("human", "{user_input}")])
        self.empty_table_gen_chat_prompt = ChatPromptTemplate.from_messages([("human", EMPTY_TABLE_GEN_PROMPT)])
        self.answer_gen_chat_prompt = ChatPromptTemplate.from_messages([
            ("system", ANSWER_GEN_W_OPERATION_SYSTEM_PROMPT),
            ("human", "{user_input}"),
        ])

        self.tab_filling_chain = self.base_chat_prompt | self.chat_model
        self.empty_table_gen_chain = self.empty_table_gen_chat_prompt | self.chat_model
        self.answer_gen_chain = self.answer_gen_chat_prompt | self.chat_model

        self.init_fewshot_entity_extraction()

        self.total_entities = []
        self.total_empty_tables = []
        self.total_table_fillings = []
        self.total_answers = []
        self.copied_data = deepcopy(data)

    def init_fewshot_entity_extraction(self):
        example_prompt = ChatPromptTemplate.from_messages([
            ("human", "{input}"),
            ("ai", "{output}"),
        ])
        self.ext_fewshot_prompt = FewShotChatMessagePromptTemplate(
            example_prompt=example_prompt,
            examples=six_shot_robust_examples,
        )
        self.entity_extraction_chat_prompt = ChatPromptTemplate.from_messages([
            ("system", ENTITY_OPERATION_EXTRACTION_SYSTEM_ROBUST_PROMPT),
            self.ext_fewshot_prompt,
            ("human", "{user_input}"),
        ])
        self.entity_extraction_chain = self.entity_extraction_chat_prompt | self.chat_model

    def get_answers(self):
        """
        Run the 5-step EASE pipeline over the dataset in batches.
        """
        batch_size = self.args.get("batch_size", 4)
        batch_inds = list(range(0, len(self.questions), batch_size))

        for batch_ind in tqdm(batch_inds, total=len(batch_inds), desc="Running EASE"):
            batch_questions = self.questions[batch_ind : batch_ind + batch_size]
            batch_table_dicts = self.tables[batch_ind : batch_ind + batch_size]

            # 1. Entity & Operation Extraction
            entity_extraction_prompts = create_entity_extraction_prompt(batch_questions, batch_table_dicts)
            entity_extraction_output = handle_rate_limit(self.entity_extraction_chain, entity_extraction_prompts)
            entity_extraction_contents = [x.content for x in entity_extraction_output]
            entities, operations = postprocess_entity_operation_extraction(entity_extraction_contents)

            # 2. Sub-table Schema Generation
            empty_table_gen_output = handle_rate_limit(self.empty_table_gen_chain, entities)
            empty_table_gen_contents = [x.content for x in empty_table_gen_output]

            # 3. Column Value Selection (symbolic, pandas-based; see filter_table_by_columns)
            empty_table_columns = [parse_columns(x) for x in empty_table_gen_contents]

            # 4. Sub-table Filling
            table_filling_prompts = [
                create_table_filling_prompt(a, b, c)
                for a, b, c in zip(entities, batch_table_dicts, empty_table_columns)
            ]
            table_filling_output = handle_rate_limit(self.tab_filling_chain, table_filling_prompts)
            table_filling_contents = [x.content for x in table_filling_output]

            # 5. Answer Generation
            answer_gen_prompts = [
                create_answer_gen_prompt(x, y, z)
                for x, y, z in zip(table_filling_contents, batch_questions, operations)
            ]
            answer_gen_output = handle_rate_limit(self.answer_gen_chain, answer_gen_prompts)
            answer_gen_contents = [x.content for x in answer_gen_output]

            self.total_entities.extend(entity_extraction_contents)
            self.total_empty_tables.extend(empty_table_gen_contents)
            self.total_table_fillings.extend(table_filling_contents)
            self.total_answers.extend(answer_gen_contents)
            time.sleep(1)

    def save_predictions(self):
        for i, case in enumerate(self.copied_data):
            all_preds = {
                "entities": self.total_entities[i],
                "empty_tables": self.total_empty_tables[i],
                "table_fillings": self.total_table_fillings[i],
                "answer": self.total_answers[i],
            }
            case["predictions"] = all_preds

        save_dir = self.args.get("save_dir", "./output")
        save_name = self.args.get("save_name", "predictions.json")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, save_name)

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(self.copied_data, f, ensure_ascii=False, indent=4)
        print(f"Successfully saved predictions to {save_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EASE: Entity-Aware Sub-table Generation for Real-world Multi-table QA")
    parser.add_argument("--config_file", type=str, required=True, help="Config json file path (e.g. gpt4o/EASE_randomly_sampled)")
    parsed_args = parser.parse_args()

    config_path = parsed_args.config_file
    if not config_path.endswith(".json"):
        config_path = os.path.join("./configs", f"{config_path}.json")

    with open(config_path, "r", encoding="utf-8") as f:
        args = EasyDict(json.load(f))

    if "jsonl" in args.data_dir:
        with open(args.data_dir, "r", encoding="utf-8") as f:
            data = [json.loads(line) for line in f]
    else:
        with open(args.data_dir, "r", encoding="utf-8") as f:
            data = json.load(f)

    ease = EASE(args, data)
    ease.get_answers()
    ease.save_predictions()
