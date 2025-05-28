from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import pandas as pd
from io import BytesIO
import re
import asyncio
import json

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

def clean_result_string(s):
    # Başında ```json varsa çıkar
    if s.startswith("```json"):
        s = s[len("```json"):].lstrip("\n")
    # Sonunda ``` varsa çıkar
    if s.endswith("```"):
        s = s[:-3].rstrip("\n")
    return s

async def stream_analysis(contents:bytes, api_key: str):
    yield "data: 📁 CSV dosyası başarıyla alındı.\n\n"
    await asyncio.sleep(2)

    try:
        df = pd.read_csv(BytesIO(contents))
    except Exception as e:
        yield f"data: ❌ CSV dosyası okunurken hata oluştu: {str(e)}\n\n"
        return
    
    yield "data: 📊 Dosya okundu. Temizleme işlemi başlatılıyor...\n\n"
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
    try:

        result = send_to_ai_for_analyze(api_key=api_key, prompt=cleaning_prompt)
        cleaning_code = result.strip("```python").strip("```").strip()
        
        # Temizleme: inplace parametre tekrarlarını düzeltelim
        cleaning_code = re.sub(r'(inplace\s*=\s*True\s*,\s*)+inplace\s*=\s*True', 'inplace=True', cleaning_code)

        exec_globals = {"pd": pd, "df": df}
      
        exec(cleaning_code, exec_globals)
        df = exec_globals["df"]
        
        yield "data: ✅ Temizleme işlemi başarıyla tamamlandı.\n\n"
        await asyncio.sleep(1)

    except Exception as e:
        yield f"data: ❌ AI destekli veri temizleme sırasında hata: {str(e)}\n\n"
        return
    
    yield "data: ☁️ Temizlenmiş veri sunucuya yükleniyor...\n\n"
    await asyncio.sleep(1)

        
    supabase_url = upload_csv_to_supabase(contents)

    if not supabase_url:
        yield "data: ❌ Veri yüklenirken hata oluştu. Lütfen tekrar deneyin.\n\n"
        return
    
    yield "data: ✅ Veri başarıyla yüklendi.\n\n"
    await asyncio.sleep(1)

    prompt = f"""
    You are a data analyst assistant. Given a CSV file available at this URL: {supabase_url}, with the following columns and sample data, generate 3 to 5 meaningful, data-specific, and easy-to-read dashboard chart ideas and accompanying insights.

    Limitations:
    - Only use these chart types: "Bar Chart", "Line Chart", "Pie Chart"
    - Suggest a maximum of 5 chart ideas

    Each chart idea should include:
    - Title
    - Chart type (from allowed types)
    - X-axis and Y-axis mapping
    - Optional: group_by or filter fields

    Insights:
    - Write between half a page to one full page of analysis
    - Focus on actual trends or patterns you can infer from the data
    - Avoid generic descriptions like “this chart shows trends”
    - Use real insights such as:
        - "Sales dropped by 25% between January and March"
        - "Product Category A generated twice the revenue of others"
        - "Cancelled orders spiked in Q3, possibly due to shipment delays"

    Language:
    - If the dataset clearly contains a specific natural language (e.g., Turkish), write the entire response in that language
    - If mixed or unclear, default to English

    Output Format:
    Return a **single JSON object** containing:
    1. "charts": a JSON array of chart definitions
    2. "insights": a Markdown-formatted string (as a single text field)

    Example Output Format:
```json
{{
  "charts": [
    {{
      "title": "Monthly Sales Trend",
      "chart_type": "Line Chart",
      "x_axis": "Month",
      "y_axis": "Sales",
      "group_by": "Region"
    }}
  ],
  "insights": "### Insights\\nSales increased steadily from January to June, with a sharp dip in July likely due to supply chain issues..."
}}

    CSV Info:
    - CSV URL: {supabase_url}
    - Sample Data:
    {sample_data}
    - Columns:
    {columns}
    """

    try:
        result = send_to_ai_for_analyze(api_key=api_key, prompt=prompt)
        analyze_result = analyze_dataframe(df)
    except Exception as e:
        yield f"data: ❌ AI analiz sürecinde hata: {str(e)}\n\n"
        return

    yield "data: 📈 Grafik önerileri ve analiz başarıyla oluşturuldu.\n\n"
    await asyncio.sleep(1)

    yield "data: ✅ Tüm işlemler tamamlandı. Detaylı analiz sayfasına yönlendiriliyorsunuz...\n\n"

    for col in df.select_dtypes(include=["datetime", "datetimetz"]).columns:
        df[col] = df[col].astype(str)

    cleaned_json_str = clean_result_string(result)

    try:
        json_obj = json.loads(cleaned_json_str)
    except json.JSONDecodeError as e:
        print("JSON parse hatası:", e)
        json_obj = None

    final_data = {
        "result": json_obj,
        "analyze_result": analyze_result,
        "cleaned_data": df.to_dict(orient="records")
    }

    yield f"data_last: {json.dumps(final_data)}\n\n"


@app.post("/upload-stream")
async def upload_stream(file: UploadFile = File(...), api_key: str = Form(...)):
    contents = await file.read()
    return StreamingResponse(stream_analysis(contents, api_key), media_type="text/event-stream")
