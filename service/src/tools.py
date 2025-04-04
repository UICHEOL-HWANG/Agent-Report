from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain_community.tools import TavilySearchResults

import requests
from youtube_transcript_api import YouTubeTranscriptApi
    
from .config import load_dotenv, google_search

import smtplib
import os
from dotenv import load_dotenv
from email.message import EmailMessage


load_dotenv(override=True)
sender_email=os.environ.get('SENDER_EMAIL')
sender_pw=os.environ.get('SENDER_PASSWORD')

def youtube_script(query: str) -> str:
    """
    유튜브에서 관련 영상을 검색하고 자막을 요약하여 반환합니다.
    """

    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "q": query,
        "type": "video",
        "part": "snippet",
        "key": google_search,  # 실제 API 키
        "maxResults": 3,
        "fields": "items(id,snippet(title))",
        "videoEmbeddable": True,
        "order": "date"
    }

    response = requests.get(url, params=params)
    items = response.json().get("items", [])
    ids = [item["id"]["videoId"] for item in items if "videoId" in item["id"]]

    script_lst = []
    for video_id in ids[:3]:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["ko"])
            combined_text = " ".join([entry["text"] for entry in transcript])[:2000]  # 길이 제한
            script_lst.append(Document(page_content=combined_text))
        except Exception as e:
            print(f"자막 오류: {video_id} → {e}")
            continue

    # 내부에서 llm 생성
    llm = ChatOpenAI(model_name="gpt-4o-mini-2024-07-18", temperature=0) # 1차 정리

    map_prompt = """
    다음은 유튜브 자막입니다:

    {text}

    이 내용을 다음 기준으로 요약해주세요:
    - 제목
    - 요약 (서론)
    - 중요 포인트 (본문)
    - 결론 및 인사이트
    (전체 2000자 이내)
    """

    map_prompt_template = PromptTemplate(template=map_prompt, input_variables=["text"])

    summary_chain = load_summarize_chain(
        llm=llm,
        chain_type="map_reduce",
        map_prompt=map_prompt_template,
        combine_prompt=map_prompt_template,
        verbose=True
    )

    return summary_chain.invoke(script_lst)

def tavily_search(query: str, max_results: int = 2, chunks_per_source: int =1) -> str:
    """
    주어진 쿼리로 Tavily API를 호출하여 관련 웹 페이지 정보를 검색하고,
    요약된 URL과 콘텐츠를 문자열로 반환합니다.
    max_result는 2개로 지정하고
    chunks_per_source는 1로 지정하고 봐야합니다
    """
    client = TavilySearchResults(
        max_results=2,
        chunks_per_source=1
    )

    response = client.invoke({"query": query})
    results = []

    for result in response:
        results.append(f"URL: {result['url']}\nContent: {result['content']}\n")
    return "\n".join(results)


# 메일 전송 함수수
def send_email(to_email,message):

    try:
        # 이메일 메세지 생성
        msg=EmailMessage()
        msg['From']=sender_email
        msg['To']=to_email
        # msg['Subject'] = keward # 검색 키워드를 제목으로?
        msg.set_content(message)

        # SMTP 서버 설정 (gmail기준)
        with smtplib.SMTP_SSL('smtp.gmail.com',465) as server:
            server.login(sender_email, sender_pw)
            server.send_message(msg)
        return '이메일 전송 성공공'
    except Exception as e:
        return f'이메일 전송 실패: {str(e)}'

        