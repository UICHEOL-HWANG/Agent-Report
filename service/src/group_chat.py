from autogen import GroupChat, GroupChatManager
from .agent_manager import agents
from .config import llm_config

groupchat = GroupChat(  # ✅ 여기도 변경!
    agents=agents,
    messages=[],
    max_round=5,
)

manager = GroupChatManager(
    groupchat=groupchat,
    name="Project_Manager",
    llm_config={"config_list": llm_config["config_list"]}
)
