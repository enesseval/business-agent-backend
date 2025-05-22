from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from agents.analysis_service import send_to_ai_for_analyze
import pandas as pd
from io import BytesIO
import re

app = FastAPI(title="CSV Analiz API", description="CSV dosyasını AI ile analiz eden servis", version="1.0.0")

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload")
async def analyze_csv(file: UploadFile = File(...), api_key: str = Form(...)):
    # 1. CSV kontrolü
    if not file.filename.endswith(".csv"):
        return {"error": "Sadece CSV dosyaları kabul edilmektedir."}

    try:
        # 2. Dosyayı oku ve DataFrame'e çevir
        contents = await file.read()
        df = pd.read_csv(BytesIO(contents))

        columns = df.columns.tolist()
        sample_data = df.head(5).to_dict(orient="records")

        cleaning_prompt = f"""
        Below are the column names and a sample of the first 5 rows of a CSV dataset.
        Please write Python code that:
        - Uses only pandas (no other libraries).
        - Performs basic cleaning: missing values, type conversion (especially dates and numbers), and trimming strings.
        - Operates on a DataFrame named `df`.
        - Does not return or print anything.
        - Assumes columns match the names exactly.
        - Ends with a cleaned `df`.

        Columns: {columns}
        Sample data: {sample_data}

        Only return valid Python code.
        """

        result = send_to_ai_for_analyze(api_key=api_key,prompt=cleaning_prompt)

        cleaning_code = result.strip("```python").strip("```").strip()

        cleaning_code = re.sub(r'\binplace=True\s*,\s*inplace=True', 'inplace=True', cleaning_code)

        exec_globals = {"pd": pd, "df": df}
        exec(cleaning_code, exec_globals)

        return {
            "cleaned_sample": exec_globals["df"].head(5).to_dict(orient="records")
        }

    except Exception as e:
        return {"error": f"Dosya okunamadı: {str(e)}"}
