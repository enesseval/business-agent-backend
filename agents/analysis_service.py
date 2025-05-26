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