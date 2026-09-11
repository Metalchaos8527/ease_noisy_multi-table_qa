import os
import json
import re
import argparse
from collections import Counter
from tqdm import tqdm
from evaluate import load
from easydict import EasyDict


def postprocess_cot_answer(pred):
    """
    Extract answer JSON block from CoT style predictions.
    """
    pattern = r"```json(\n)(.*?)(\n)```"
    tuple_pattern = r'\(\s*([^\(\)]+?)\s*\)'
    quote_pattern = r'\w(\")\w'
    replacement = r'[\1]'

    match = re.search(pattern, pred, re.DOTALL)
    if not match:
        pattern = r"```json(.*?)```"
        match = re.search(pattern, pred, re.DOTALL)
    if not match:
        return pred

    answer_str = match.group()
    answer_str = answer_str.replace("```", "").strip()
    answer_str = answer_str.replace("json", "").strip()
    answer_str = answer_str.replace("'", '"').strip()
    answer_str = answer_str.replace("…", "").strip()
    answer_str = re.sub(quote_pattern, "'", answer_str)
    answer_str = re.sub(tuple_pattern, replacement, answer_str)
    answer_str = answer_str.replace("None", "null")

    try:
        answer_json = json.loads(answer_str)
        return str(answer_json.get("answer", answer_str))
    except Exception:
        return answer_str


def postprocess_answer(answer_content):
    """
    Extract string after 'Final Answer:' in prediction.
    """
    pattern = r"Final Answer[:\s]*(.*)"
    match = re.search(pattern, answer_content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return answer_content.strip()


def exact_match_score_contain_version(ground_truth, prediction):
    """
    Compute substring exact match score.
    """
    ground_truth_list = [g.strip() for g in ground_truth.split(",") if g.strip()]
    if len(ground_truth_list) > 1:
        correct_counts = sum(1 for gt in ground_truth_list if gt in prediction)
        return correct_counts / len(ground_truth_list)
    else:
        return 1.0 if ground_truth in prediction else 0.0


def f1_score(prediction, ground_truth):
    """
    Token-level / Item-level F1 score.
    """
    common = Counter(prediction) & Counter(ground_truth)
    num_same = sum(common.values())
    if num_same == 0 or len(prediction) == 0 or len(ground_truth) == 0:
        return 0.0
    precision = 1.0 * num_same / len(prediction)
    recall = 1.0 * num_same / len(ground_truth)
    return (2 * precision * recall) / (precision + recall)


def evaluate_prediction(prediction, reference, table, question):
    """
    Evaluate F1 score considering relevant vs non-relevant elements in tables.
    """
    table_set = set(table)
    ref_set = set(reference)

    non_reference_elements = table_set - ref_set
    reference_elements = [r for ref in ref_set for r in ref.replace(':', '').split()]
    non_reference_elements = non_reference_elements - set(reference_elements)

    for element in non_reference_elements.copy():
        if element.rstrip('.') in question or element.rstrip('.') in str(reference):
            non_reference_elements.discard(element)

    reference_included = []
    for item in reference:
        target = item.replace('.0', '') if item.endswith('.0') else item
        if target in prediction or re.sub(r'(?<=\d),(?=\d)', '', target) in prediction \
                or all(part in prediction for part in re.split(r'\s+and\s+', target)):
            reference_included.append(item)

    non_reference_included = [str(item) for item in non_reference_elements
                              if re.search(r'(?<!\w)' + re.escape(str(item)) + r'(?!\w)', prediction)]
    prediction_included = reference_included + non_reference_included

    return f1_score(prediction_included, reference)


class Evaluator:
    def __init__(self, args):
        self.args = args

    def evaluate(self):
        chrf = load("chrf")
        save_file_name = self.args.data_file.split(".json")[0]
        data_path = os.path.join(self.args.data_dir, self.args.data_file)

        with open(data_path, 'r', encoding='utf-8') as f:
            pred_file = json.load(f)

        total_substring_em_score = 0.0
        total_chrf_score = 0.0
        total_f1_score = 0.0

        for item in tqdm(pred_file, total=len(pred_file), desc="Evaluating"):
            scores_dict = {}
            question = item['question']
            tables = item.get('tables', []) + item.get('noise_tables', [])
            reference = item.get('short_answer', '')

            raw_pred = item.get("predictions", {}).get("answer", "")
            if "EASE" in self.args.get("model_name", "EASE"):
                try:
                    prediction = postprocess_answer(raw_pred).replace("\n", " ")
                except Exception:
                    prediction = ""
            elif "cot" in self.args.get("model_name", "").lower():
                prediction = postprocess_cot_answer(raw_pred)
            else:
                try:
                    quote_proc = raw_pred.replace("'", '"')
                    pred_json = json.loads(quote_proc)
                    prediction = str(pred_json.get("answer", raw_pred))
                except Exception:
                    prediction = raw_pred.replace("\n", " ")

            table_data = []
            for t in tables:
                t_json = json.loads(t) if isinstance(t, str) else t
                sub_table = [val for sublist in t_json.get('data', []) for val in sublist]
                for data in sub_table.copy():
                    if not isinstance(data, str) or data.isnumeric() or len(data) <= 1:
                        sub_table.remove(data)
                table_data.append(sub_table)

            table_data = [d for sublist in table_data for d in sublist]

            # Reference normalization
            if ',' in reference and ';' in reference:
                ref_list = [sub_item for it in reference.split('; ') for sub_item in it.split(', ')]
            else:
                ref_list = reference.split(', ')
            if ref_list and ref_list[-1].endswith('.'):
                ref_list[-1] = ref_list[-1][:-1]

            # Metric calculations
            if prediction == ref_list or prediction == reference:
                score = 1.0
            else:
                score = evaluate_prediction(prediction, ref_list, table_data, question)
            total_f1_score += score

            substring_em_score = exact_match_score_contain_version(reference, prediction)
            chrf_score = chrf.compute(predictions=[prediction], references=[reference])['score']

            scores_dict['substring_em_score'] = substring_em_score
            scores_dict["chrf_score"] = chrf_score
            scores_dict["table_eval_f1_score"] = score
            item["eval_result"] = scores_dict

            total_substring_em_score += substring_em_score
            total_chrf_score += chrf_score

        n_samples = len(pred_file)
        avg_em = (total_substring_em_score / n_samples) * 100
        avg_chrf = total_chrf_score / n_samples
        avg_f1 = (total_f1_score / n_samples) * 100

        print(f"\n================ Evaluation Results ================")
        print(f"Model: {self.args.get('model_name', 'EASE')} | Setting: {self.args.get('setting', 'noisy')}")
        print(f"- Substring EM Score: {avg_em:.2f}%")
        print(f"- chrF Score        : {avg_chrf:.2f}")
        print(f"- Table Eval F1     : {avg_f1:.2f}%")
        print(f"====================================================\n")

        save_dir = self.args.get("save_dir", "./result")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, f"{save_file_name}_eval.json")
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(pred_file, f, ensure_ascii=False, indent=4)
        print(f"Successfully saved evaluation report to {save_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluation for Multi-Table QA")
    parser.add_argument("--config_file", type=str, required=True, help="Evaluation config json file (e.g. gpt4o/EASE_randomly_sampled)")
    parsed_args = parser.parse_args()

    config_path = parsed_args.config_file
    if not config_path.endswith(".json"):
        config_path = os.path.join("./eval_configs", f"{config_path}.json")

    with open(config_path, "r", encoding="utf-8") as f:
        args = EasyDict(json.load(f))

    evaluator = Evaluator(args)
    evaluator.evaluate()
