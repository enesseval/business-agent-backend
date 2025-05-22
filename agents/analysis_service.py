# analysis_service.py

import google.generativeai as genai

def send_to_ai_for_analyze(api_key:str,prompt:str) -> str:

    if not api_key:
        return {"error":"API Key is missing"}
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash-preview-04-17")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        raise RuntimeError(f"AI gönderirken hata oluştu: {str(e)}")

# def analyze_csv_file(file_bytes: bytes, api_key: str):
#     """
#     Analyzes a CSV file using Google's Gemini AI to clean the data and return insight-ready output.
#     """

#     # Step 1: Read CSV content into DataFrame
#     df = pd.read_csv(BytesIO(file_bytes))

#     # Step 2: Extract columns and sample data for prompt
#     columns = df.columns.tolist()
#     sample_data = df.head(5).to_dict(orient="records")

#     # Step 3: Configure Gemini AI
#     genai.configure(api_key=api_key)
#     model = genai.GenerativeModel("gemini-2.5-flash-preview-04-17")

#     # Step 4: English Prompt for cleaning code
#     cleaning_prompt = f"""
#     Below are the column names and a sample of the first 5 rows of a CSV dataset.
#     Please write Python code that:
#     - Uses only pandas (no other libraries).
#     - Performs basic cleaning: missing values, type conversion (especially dates and numbers), and trimming strings.
#     - Operates on a DataFrame named `df`.
#     - Does not return or print anything.
#     - Assumes columns match the names exactly.
#     - Ends with a cleaned `df`.

#     Columns: {columns}
#     Sample data: {sample_data}

#     Only return valid Python code.
#     """

#     # Step 5: Generate cleaning code with Gemini
#     code_response = model.generate_content(cleaning_prompt)
#     cleaning_code = code_response.text.strip("```python").strip("```").strip()

#     # Step 6: Sanitize code (remove double inplace=True)
#     cleaning_code = re.sub(r'\binplace=True\s*,\s*inplace=True', 'inplace=True', cleaning_code)

#     # Step 7: Execute cleaning code
#     exec_globals = {"pd": pd, "df": df}
#     exec(cleaning_code, exec_globals)

#     # Step 8: Return structured response
#     return {
#         "session_id": str(uuid.uuid4()),
#         "columns": columns,
#         "sample_data": sample_data,
#         "cleaning_code": cleaning_code,
#         "cleaned_sample": exec_globals["df"].head(5).to_dict(orient="records")
#     }
