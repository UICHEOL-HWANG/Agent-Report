from autogen import AssistantAgent, UserProxyAgent, register_function
from .config import llm_config
from .tools import tavily_search, youtube_script, news_search_serper

classification_agent = AssistantAgent(
    name="classification_agent",
    llm_config = {
        "config_list" : llm_config["config_list"]
    },
    code_execution_config={"use_docker": False},  # Docker 안 쓰는 코드 실행
system_message = """
당신은 분류 에이전트입니다. 사용자의 요청을 분석하여 다음 세 가지 카테고리 중 하나로 분류하고, 해당 에이전트에게 키워드 형태로 내용을 전달해야 합니다.

아래 규칙을 철저히 따르세요:

1. "영상" 또는 "유튜브" 관련 키워드가 포함되면 → **youtube_research 에게 전달**
2. "뉴스" 또는 "기사" 관련 키워드가 포함되면 → **news_search_agent 에게 전달**
3. "검색", "찾아줘", "검색해서" 등의 일반 정보 요청이면 → **research_agent 에게 전달**

반드시 원문에서 핵심 키워드를 추출하여 전달하며, **직접 답변하지 말고** 전문 에이전트에게만 전달하세요.

또한, 이전 대화 내용이 이어지는 경우에는 그 문맥을 고려하여 키워드를 추출하세요.

출력 포맷 예시:
- 전달 키워드: "오늘 뉴스 영상"
- 전달 대상: youtube_research

----------------------
📌 예시

User: 오늘 뉴스 영상 내용 좀 요약해줘  
→ 전달 키워드: "오늘 뉴스 영상"  
→ 전달 대상: youtube_research

User: 오늘의 뉴스 내용 요약해줘  
→ 전달 키워드: "오늘의 뉴스"  
→ 전달 대상: news_search_agent

User: 잡채 요리방법 검색해서 요약해줘  
→ 전달 키워드: "잡채 요리방법"  
→ 전달 대상: research_agent

User: 계속 알려줘  
→ 이전 대화에서 유튜브 검색을 했으면 그에 이어서 "이전 유튜브 키워드"로 youtube_research 에게 전달
"""

)

research_agent = AssistantAgent(
    name="research_agent",
    llm_config = {
        "config_list" : llm_config["config_list"]
    },
    system_message="""
   당신은 tavily_search 툴을 이용해서 검색한 내용을 정리하는 전문가입니다.
   classification_agent에게 내용을 전달 받으면, tavily_search 툴을 호출하고, 그 결과를 요약해서 user에게 알려주고  summarizer_agent에게 내용을 전달하세요
    """,
    code_execution_config={"use_docker": False},  # Docker 안 쓰는 코드 실행
)

user_proxy = UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",   # 대화형 CLI 사용
    code_execution_config=False,
    system_message="""
    당신은 사용자 역할을 하는 프록시 에이전트입니다.
    사용자의 질문을 GroupChatManager로 전달하고,
    응답을 사용자에게 자동으로 보여주는 기능을 합니다.
    사용자가 "그만", "종료"라고 말하면 대화를 종료합니다.
    """
)

youtube_researcher = AssistantAgent(
    name='youtube_research',
    llm_config = {
        "config_list" : llm_config["config_list"]
    },
    code_execution_config={"use_docker": False},
    system_message="""
    당신은 youtube_script 툴을 이용해서 검색한 내용을 정리하는 전문가 입니다.
    classification_agent에게 내용을 전달 받으면 youtube_script 툴을 호출하고, 그 결과를 요약해서 user에게 알려주고 summarizer_agent에게 내용을 전달하세요.
    """
)


summarizer_agent = AssistantAgent(
    name="summarizer_agent",
    llm_config={
        "config_list": llm_config["config_list"][0]  # lightweight model 추천
    },
    code_execution_config={"use_docker": False},
    system_message="""
    당신은 검색 결과를 요약해주는 요약 전문가입니다.
    각 에이전트들이 툴로 가져온 결과를 바탕으로 핵심 정보만 간결하게 정리해 사용자에게 전달해주세요.
    요약 방법은 제목, 서론, 본론, 결론, 출처 URL로 크게 나누어 마크다운 형태로 반환하고, 1000자 이내로 정리하세요.
    제목에 날짜는 넣을 필요 없습니다.
    """
)

news_search_agent = AssistantAgent(
    name="news_search_agent",
    llm_config={
        "config_list": llm_config["config_list"]
    },
    code_execution_config={"use_docker": False},
    system_message="""
당신은 최신 뉴스를 검색하고, 그 결과를 정리해주는 뉴스 검색 전문 에이전트입니다.

다음과 같은 절차를 따르세요:

1. 사용자의 요청에서 핵심 키워드를 파악하세요.
2. Serper 뉴스 검색 툴을 호출하여 최근 뉴스 기사들을 수집하세요.
3. 각 뉴스 기사에서 요약(snippet)과 링크를 정리해 사용자에게 보여주세요.

출력은 다음 형식으로 작성하세요:

- 요약 내용 (snippet)
👉 출처 링크

요약한 다음 summarizer_agent에게 넘겨주세요. 

"""
)


## 실희님 승현쿤 작업

register_function(
  tavily_search,
  caller=research_agent,
  executor=user_proxy,
  description="Tavily API를 통해 웹에서 관련 정보를 검색하고 요약된 결과를 문자열로 반환합니다.",
)

register_function(
    youtube_script,
    caller=youtube_researcher,
    executor=user_proxy,
    description="youtube api를 통해 유트브 검색 기반으로 얻은 정보를 검색하고 요약된 결과를 문자열로 반환합니다."
)

register_function(
    news_search_serper,
    caller=news_search_agent,  # 예: validator_agent, research_agent 등
    executor=user_proxy,
    description="Serper 뉴스 검색을 통해 최신 뉴스의 요약(snippet)과 링크를 반환합니다. 하루 이내 뉴스만 포함됩니다."
)

agents = [classification_agent, research_agent, youtube_researcher, news_search_agent,  summarizer_agent, user_proxy]