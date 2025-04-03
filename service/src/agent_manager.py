from autogen import AssistantAgent, UserProxyAgent, register_function
from .config import llm_config
from .tools import tavily_search
from .tools import youtube_script

classification_agent = AssistantAgent(
    name="classification_agent",
    llm_config = {
        "config_list" : llm_config["config_list"]
    },
    code_execution_config={"use_docker": False},  # Docker 안 쓰는 코드 실행
    system_message="""
    당신은 입력된 문장을 카테고리에 따라 분류하는 분류 에이전트다.
    다음 중 하나의 카테고리를 골라서 출력한 뒤 각 전문 에이전트들에게 내용을 전달해야 한다.
    대화형식으로 내용이 도착해도 검색형태로 변환해서 에이전트에게 전달해야하며 당신은 답변을 남기면 안됩니다.

    1. 유튜브 검색
    2. 일반검색

    예시:
    User : 오늘 뉴스 내용 좀 요약해줘 -> 영상 검색과 관련된 내용 "영상" 이라는 키워드가 반드시 들어가야 넘겨줘야 합니다
    키워드 : 오늘의 뉴스
    Youtube_agent에게 내용 전달

    그 외 나머지는 일반검색으로 넘기기

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
    요약 방법은 제목, 서론, 본론, 결론으로 크게 나누어 마크다운 형태로 반환하세요. 1000자 이내로 정리하세요
    youtube_research에게 전달 받은 내용은 자막
    """
)

## 이메일 작성을 위한 에이전트를 만들 계획 

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

agents = [classification_agent, research_agent, youtube_researcher, summarizer_agent, user_proxy]