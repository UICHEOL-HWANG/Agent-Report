from autogen import GroupChat, GroupChatManager
from .agent_manager import agents
from .config import llm_config

groupchat = GroupChat(  # ✅ 여기도 변경!
    agents=agents,
    messages=[],
    max_round=6
)

manager = GroupChatManager(
    groupchat=groupchat,
    name="Project_Manager",
    system_message=(
        "user_proxy에서 '그만' 또는 '종료' 라는 명령어가 나오면 종료해주세요.",
        "에이전트들이 모두 실행을 마친 뒤 차례대로 실행해야 합니다."
    ),
    llm_config={"config_list": llm_config["config_list"]}
)
