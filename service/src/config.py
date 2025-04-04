from dotenv import load_dotenv
import os 

load_dotenv()


llm_config = {
    "config_list": [{"model": "gpt-4o-mini-2024-07-18", "api_key": os.environ["OPENAI_API_KEY"]}],
}

google_search = os.getenv("GOOGLE_SEARCH_API")

serper = os.getenv("SERPER_AI")
sender = os.getenv("EMAIL_ADDRESS")
password = os.getenv("EMAIL_PASSWORD")