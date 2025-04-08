from dotenv import load_dotenv
import os
import streamlit as st

# .env 파일 로드 (로컬에서만 작동)
load_dotenv()

def get_env_var(key):
    # 배포 환경이면 st.secrets 사용, 아니면 os.environ
    return st.secrets[key] if key in st.secrets else os.getenv(key)

# OpenAI API 설정
llm_config = {
    "config_list": [{
        "model": "gpt-4o-mini-2024-07-18",
        "api_key": get_env_var("OPENAI_API_KEY")
    }],
}

# 기타 환경 변수
GOOGLE_SEARCH_API = get_env_var("GOOGLE_SEARCH_API")
SERPER_API = get_env_var("SERPER_AI")
EMAIL_ADDRESS = get_env_var("EMAIL_ADDRESS")
EMAIL_PASSWORDS = get_env_var("EMAIL_PASSWORD")
