EMPTY_TABLE_GEN_PROMPT = """Generate a small empty table format to answer queries with the extracted entities as columns. Each entitiy is formated as Table_name.Column_name. The empty table should be represented in standard tabular format.
The output format should be like: ```| entity1 | entity 2 | entity3 | ... | entity n|
|---------|------------------|-------| ... |---------------------|
|         |                  |       | ... |                     |```
Just give me the output.

Input:{user_input}"""

ENTITY_OPERATION_EXTRACTION_SYSTEM_ROBUST_PROMPT = """Task description:
You are an expert data scientist. You will be given a Question and Example Tables(subsets of the original tables). Your job is to extract important entities and desired operations from a given question. The extracted entities and operations will be used as groundwork for constructing a reasoning table to write a faithful and precise answer to the given question. Below is the procedure for extracting entities and operations from the question.

Procedure.
1. Find the relevancy between the question and tables
    - Read the question first, then look at the column names and data types in the table.
    - Find the column names that might be useful sources for answering it.
2. Extract operations that should be used when answering the question in the order of reasoning. The operation might be about counting, comparison, sorting, arithmetic operations, grouping, etc.
    - If the question merely requires a selection of the value within the table, the operation should be 'select'.
3. Extract the important entities in the question. The extraction must follow these criteria:
1) Discard the entity that is irrelevant to any columns of the given tables. 
2) Do not discard the entity that can be reasoned by using the values from the given tables' columns.
3) If the entity's name is the same as the table's name, extract the relevant column name from that corresponding table.
4) If the extracted entity emerges from more than two tables, extract all the co-occurred entities, and the table name should delimit the entities.
5) Extract entity as 'Table_name.Column_name' format.

**Note**
- Please be aware that the provided example tables are just subsets of the original, complete tables. Therefore, the entities you wish to extract may not be present in the row of the tables.
- This should not lead to extraction and operation failure: not extracting any entities or operations because of the absence of the value in the given example tables.
- Do not generate "None" or "Unanswerable" for the **Operations** and **Extracted Entities**. You must extract at least one entity or operation. 

Output format:
- **Explanation**: Describe step by step reasoning chain of the extraction
- **Operations**: #o1: Operation name,
#o2: Operation name, ...
#oj: Operation name.
- **Extracted Entities**: #e1: Entity name,
#e2: Entity name, ...
#ei: Entity name.
"""

ANSWER_GEN_W_OPERATION_SYSTEM_PROMPT = """You are a data analysis expert. Please answer the question using step-by-step reasoning based on the provided table and the list of potentially required operations.

Instructions:
 1. Parse the structured data carefully.
 2. Identify relationships between tables and question.
 3. Provide a step-by-step reasoning process based on the provided operations.
 4. Answer the question using data from all tables. When generating the Final Answer, write conciesly and precisely. 

The output should be like
Reasoning step:
Final Answer:"""

TABLE_FILLING_PROMPT = """Fill the table using the given data. Extract and organize information from the Source Data and fill the Empty table.

Input: 
* Source Data (Provided Tables): {tables}
* Empty Table Structure (Columns): {empty_table}

Output Format: 
1. Filled Table: Provide the completed table in this markdown format: 
```| Column 1 | Column 2 | ... | Column N | |------------|------------|-----|------------| | Value 1 | Value 2 | ... | Value N | | ... | ... | ... | ... |```
2. Reasoning Steps: Explain how you filled the table step-by-step for each column and any rules applied to handle missing or conflicting data."""
