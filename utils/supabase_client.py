from supabase import create_client, Client
from dotenv import load_dotenv
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
