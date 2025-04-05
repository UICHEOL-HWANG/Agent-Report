from dotenv import load_dotenv
import os 

load_dotenv()

llm_config = {
    "config_list": [{"model": "gpt-4o-mini-2024-07-18", "api_key": os.environ["OPENAI_API_KEY"]}],
}

GOOGLE_SEARCH_API = os.getenv("GOOGLE_SEARCH_API")

SERPER_API = os.getenv("SERPER_AI")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORDS = os.getenv("EMAIL_PASSWORD")