from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import pandas as pd
from io import BytesIO
import re
import asyncio

from agents.analysis_service import send_to_ai_for_analyze
from utils.dataframe_utils import analyze_dataframe
from utils.supabase_client import upload_csv_to_supabase

app = FastAPI(title="CSV Analiz API", description="CSV dosyasını AI ile analiz eden servis", version="1.0.0")

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def stream_analysis(contents:bytes, api_key: str):
    yield "data: Dosya alındı...\n\n"
    await asyncio.sleep(2)

    try:
        df = pd.read_csv(BytesIO(contents))

        yield "data: Dosya okundu, analiz başlıyor...\n\n"
        await asyncio.sleep(2)

        yield "data: AI ile analiz ediliyor...\n\n"
        await asyncio.sleep(1)

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

        result = send_to_ai_for_analyze(api_key=api_key, prompt=cleaning_prompt)
        cleaning_code = result.strip("```python").strip("```").strip()
        
        # Temizleme: inplace parametre tekrarlarını düzeltelim
        cleaning_code = re.sub(r'(inplace\s*=\s*True\s*,\s*)+inplace\s*=\s*True', 'inplace=True', cleaning_code)

        exec_globals = {"pd": pd, "df": df}
        try:
            exec(cleaning_code, exec_globals)
            # exec içinde df değiştiyse onu güncelle
            df = exec_globals["df"]
        except Exception as e:
            yield f"data: Hata oluştu: AI kodu çalıştırılırken hata. Hata: {str(e)}\n\n"
            return

        yield "data: Data temizleme tamamlandı...\n\n"
        await asyncio.sleep(1)

        yield "data: Data sunucuya yükleniyor... \n\n"
        await asyncio.sleep(1)
        supabase_url = upload_csv_to_supabase(contents)
        if supabase_url:
            yield "data: Data sunucuya yüklendi...\n\n"
        else:
            yield "data: Data sunucuya yüklenirken hata oluştu...\n\n"

        prompt = f"""
        You are a data analyst assistant. Given a CSV file available at this URL: {supabase_url}, with the following columns and sample data, generate 2 to 3 meaningful chart ideas for a dashboard.

        Return:
        - For each chart, include:
        - Title
        - Chart type (e.g., bar, line, pie)
        - X-axis and Y-axis mapping
        - Optional: any groupings or filters used
        - After the JSON list of chart ideas, provide a detailed explanation of the insights these charts reveal, in at least half a page and up to one page.

        sample_data:{sample_data}
        columns:{columns}

        Return the output as:
        1) JSON list of chart ideas
        2) Detailed textual insights and analysis

        CSV URL: {supabase_url}
        """

        result = send_to_ai_for_analyze(api_key=api_key, prompt=prompt)

        print(result)

        # En son dönülecek return ile.
        analyze_result = analyze_dataframe(df)

    except Exception as e:
        yield f"data: Hata oluştu: {str(e)}\n\n"


@app.post("/upload-stream")
async def upload_stream(file: UploadFile = File(...), api_key: str = Form(...)):
    contents = await file.read()
    return StreamingResponse(stream_analysis(contents, api_key), media_type="text/event-stream")
