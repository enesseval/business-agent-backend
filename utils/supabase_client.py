from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def log_conversation(session_id,question,answer):
    try:
        supabase.table("conversation_history").insert({
            "session_id":session_id,
            "question":question,
            "answer":answer
        }).execute()
    except Exception as e:
        print(f"Log kaydı sırasında hata: {str(e)}")

def upload_csv_to_supabase(file_content:bytes,filename:str = None) -> str:
    bucket_name = "csv-files"

    if filename is None:
        filename = f"csv_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    try:
        response = supabase.storage.from_(bucket_name).upload(
            filename,
            file_content,
            {"content_type":"text/csv"}
        )

        if response:
            public_url = supabase.storage.from_(bucket_name).get_public_url(filename)
            return public_url
        else:
            raise Exception("Supabase upload başarısız.")
        
    except Exception as e:
        print(f"CSV yükleme hatası: {str(e)}")
        return None