from autogen import AssistantAgent, UserProxyAgent, register_function
from .config import llm_config
from .tools import tavily_search, youtube_script, news_search_serper
import os 

classification_agent = AssistantAgent(
    name="classification_agent",
    llm_config={
        "config_list": llm_config["config_list"]
    },
    code_execution_config={"use_docker": False},
    system_message="""
    당신은 분류 에이전트입니다. 사용자의 요청을 분석하여 다음 네 가지 카테고리 중 하나로 분류하고,
    해당 에이전트에게 **핵심 키워드 형태**로 내용을 전달해야 합니다.

    아래 규칙을 철저히 따르세요:

    1. "영상" 또는 "유튜브" 관련 키워드가 포함되면 → **youtube_research 에게 전달**
    2. "뉴스" 또는 "기사" 관련 키워드가 포함되면 → **news_search_agent 에게 전달**
    3. "검색", "찾아줘", "검색해서" 등의 일반 정보 요청이면 → **research_agent 에게 전달**

    💡 핵심 키워드는 원문에서 의미 있는 단어들을 뽑아내야 하며, 직접 답변하지 말고 전문 에이전트에게만 전달하세요.

    또한, 이전 대화 내용이 이어지는 경우에는 그 문맥을 고려하여 키워드를 추출하세요.

    📌 출력 포맷 예시:

    - 전달 키워드: "첨부한 PDF"
    - 전달 대상: ragproxyagent → summarizer_agent

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
    당신은 유튜브 영상 정보를 수집하고 정리하는 전문 에이전트입니다.

    classification_agent로부터 전달받은 키워드를 바탕으로 youtube_script 툴을 호출해 관련 영상을 검색하고, 해당 영상의 자막 및 내용을 요약하세요.

    요약된 결과는 다음 두 곳에 전달해야 합니다:
    1. 사용자 (user_proxy)
    2. summarizer_agent

    요약은 가능한 한 간결하게 핵심 내용 위주로 정리해주세요. 영상의 길이와 무관하게 명확하고 요점 중심으로 전달하는 것이 중요합니다.
    """
)


summarizer_agent = AssistantAgent(
    name="summarizer_agent",
    llm_config={
        "config_list": llm_config["config_list"][0]  # lightweight model 추천
    },
    code_execution_config={"use_docker": False},
    system_message = """
    당신은 뉴스 및 영상 정보를 요약하는 전문 요약 에이전트입니다.

    검색 또는 영상 기반 뉴스 데이터에는 하나 이상의 주요 이슈가 포함되어 있을 수 있습니다.  
    당신의 임무는 이러한 주요 이슈들을 **주제별로 구분**하여 각각 아래의 형식으로 정리하는 것입니다.

    다음 마크다운 구조를 이슈별로 반복해서 작성하세요:

    ---

    # **제목**  
    전체 내용을 대표할 수 있는 간결하고 강렬한 제목 (날짜는 넣지 마세요)

    ## **서론**  
    어떤 사건/주제인지 개요 설명. 왜 중요한 뉴스인지 알려주세요.

    ## **본론**  
    주요 사실을 논리적으로 풀어 설명하세요.  
    기사나 영상에서 언급된 세부 사항, 인용, 반응, 수치 등을 포함하세요.

    ## **결론**  
    이 사건이 주는 의미나 앞으로의 전망, 함의 등을 정리하세요.

    ## **출처 URL**  
    출처 링크들을 마크다운 목록으로 나열하세요. 예:
    - https://example.com/news1
    - https://example.com/news2

    ---

    📌 작성 지침:
    - 각 주제마다 위의 구조를 반복하여 작성하세요. (예: 탄핵 이슈, 경제 이슈, 외교 이슈 등)
    - 문장은 자연스럽고 연결성 있게 작성하세요 (문단 간 흐름 중요).
    - 너무 단순하거나 건조하게 요약하지 말고, 독자가 뉴스를 제대로 이해할 수 있게 써주세요.
    - 전체 글은 **총 1000~1200자 내외로 요약**되도록 압축하세요.
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

agents = [classification_agent, research_agent, youtube_researcher, news_search_agent, summarizer_agent, user_proxy]