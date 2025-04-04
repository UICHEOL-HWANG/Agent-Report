from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from tavily import TavilyClient
import os 


import requests
import json
from typing import Annotated

import requests
from youtube_transcript_api import YouTubeTranscriptApi
    
from .config import load_dotenv, google_search, serper, sender, password
from .type_schemas import YouTubeSummaryInput

import markdown
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def youtube_script(input: Annotated[YouTubeSummaryInput, "유튜브 검색 쿼리 입력값"]) -> str:
    """
    유튜브 검색 → 자막 수집 → 요약 결과 반환
    """
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "q": input.query,
        "type": "video",
        "part": "snippet",
        "key": google_search,
        "maxResults": 3,
        "fields": "items(id,snippet(title))",
        "videoEmbeddable": True,
        "order": "date"
    }

    response = requests.get(url, params=params)
    items = response.json().get("items", [])
    ids = [item["id"]["videoId"] for item in items if "videoId" in item["id"]]
    titles = [item["snippet"]["title"] for item in items if "title" in item["snippet"]]

    script_lst = []
    for video_id, title in zip(ids, titles):
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["ko"])
            combined_text = " ".join([entry["text"] for entry in transcript])[:2000]
            script_lst.append(
                Document(
                    page_content=f"[영상 제목: {title}]\n\n{combined_text}",
                    metadata={"title": title, "video_id": video_id}
                )
            )
        except Exception as e:
            print(f"자막 오류: {video_id} → {e}")
            continue

    if not script_lst:
        return "자막이 있는 유튜브 영상을 찾을 수 없습니다."

    # 요약 체인 구성
    llm = ChatOpenAI(model_name="gpt-4o-mini-2024-07-18", temperature=0)

    map_prompt = """
    다음은 유튜브 영상의 자막입니다.
    제목에 포함된 날짜 또는 주요 키워드도 참고하여 핵심 내용을 요약해주세요.
    
    자막내용 : {text}

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


def tavily_search(
    query: str,
    max_results: int = 5,
    search_depth: str = "basic"
) -> str:
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    response = client.search(
        query=query,
        max_results=max_results,
        search_depth=search_depth,
    )

    formatted_results = []
    for result in response.get("results", []):
        formatted_results.append(
            f"Title: {result['title']}\nURL: {result['url']}\nContent: {result['content']}\n"
        )

    return "\n".join(formatted_results)



def news_search_serper(query: str) -> str:
    """_summary_
    serperai를 통해 뉴스를 검색하여 문자열로 리턴 해주는 툴 
    Args:
        query (str): 사용자 입력 

    Returns:
        str: 뉴스 결과를 합친 문자열
    """
    url = "https://google.serper.dev/news"

    payload = {
        "q": query,
        "gl": "kr",
        "hl": "ko",
        "tbs": "qdr:d"  # 최근 하루 뉴스
    }

    headers = {
        'X-API-KEY': serper, 
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    data = response.json()

    news_items = data.get("news", [])

    if not news_items:
        return "검색 결과가 없습니다."

    result = ""
    for item in news_items:
        result += f"- {item['snippet']}\n👉 {item['link']}\n\n"

    return result.strip()


## 이메일 전송 



def markdown_to_html(md_text: str) -> str:
    return markdown.markdown(md_text)

def send_email(to: str, content_markdown: str):
    senders = sender  # 발신자 이메일
    passwords = password     # 앱 비밀번호 or SMTP 패스워드
    smtp_server = "smtp.gmail.com"
    smtp_port = 587


    # 마크다운 → HTML 변환
    content_html = markdown.markdown(content_markdown)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "📝 멀티에이전트 요약 보고서"
    msg["From"] = sender
    msg["To"] = to

    # 텍스트 + HTML 버전 둘 다 첨부 (이메일 클라이언트 호환성↑)
    part1 = MIMEText(content_markdown, "plain", "utf-8")
    part2 = MIMEText(content_html, "html", "utf-8")

    msg.attach(part1)
    msg.attach(part2)

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(senders, passwords)
        server.send_message(msg)