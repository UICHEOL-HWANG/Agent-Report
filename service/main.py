import streamlit as st
from src.group_chat import manager, groupchat
from src.agent_manager import user_proxy
from src.tools import send_email
import os 

st.set_page_config(page_title="멀티 에이전트 보고서 서버", layout="centered")
st.markdown("""
<h1 style='text-align: center; color: #4A90E2;'>🤖 Multi-Agent Intelligence Service</h1>
<p style='text-align: center; font-size: 18px; color: gray;'>문서 요약 · 뉴스 검색 · 유튜브 리서치</p>
""", unsafe_allow_html=True)
 

# 세션 상태 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_message_count" not in st.session_state:
    st.session_state.last_message_count = 0

# 채팅 컨테이너 생성 (스크롤 가능)
chat_container = st.container()

# 유저 입력 받기 (항상 화면 하단에 표시)
user_input = st.chat_input("질문을 입력해주세요 ✏️")

# 채팅 메시지 출력
with chat_container:
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant"):
                st.markdown(msg["content"])

# 사용자 입력 처리
if user_input:
    clean_input = user_input.strip()

    # 화면에 유저 메시지 보여주기
    with chat_container:
        with st.chat_message("user"):
            st.markdown(clean_input)

    # 세션에 저장
    st.session_state.chat_history.append({
        "role": "user",
        "content": clean_input
    })
    
    # 현재 메시지 수 저장
    if hasattr(groupchat, "messages"):
        st.session_state.last_message_count = len(groupchat.messages)
    
    # AutoGen 대화 시작
    with st.spinner("에이전트가 응답 중입니다..."):
        # 대화 시작
        result = user_proxy.initiate_chat(manager, message=clean_input)
    
    # 새로운 메시지 추출
    if hasattr(groupchat, "messages"):
        # summarizer_agent의 메시지 찾기
        for msg in groupchat.messages:
            if msg.get("name") == "summarizer_agent":
                # 세션 상태에 저장
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": msg.get("content", "응답을 생성하지 못했습니다.")
                })
                
                # 화면에 표시
                with chat_container:
                    with st.chat_message("assistant"):
                        st.markdown(msg.get("content", "응답을 생성하지 못했습니다."))
                
                break  # 첫 번째 summarizer_agent 메시지만 사용
        
        # summarizer_agent 메시지가 없는 경우 마지막 메시지 사용
        if not any(msg.get("name") == "summarizer_agent" for msg in groupchat.messages):
            last_msg = groupchat.messages[-1] if groupchat.messages else {"content": "응답을 생성하지 못했습니다."}
            
            # 세션 상태에 저장
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": last_msg.get("content", "응답을 생성하지 못했습니다.")
            })
            
            # 화면에 표시
            with chat_container:
                with st.chat_message("assistant"):
                    st.markdown(last_msg.get("content", "응답을 생성하지 못했습니다."))
                    
# 이메일 UI를 "assistant 메시지가 존재할 때만" 보이게 설정
has_assistant_response = any(msg["role"] == "assistant" for msg in st.session_state.chat_history)

if has_assistant_response:
    st.markdown("---")
    st.subheader("📧 요약 보고서를 이메일로 받기")

    user_email = st.text_input("이메일 주소를 입력하세요", placeholder="your@email.com")

    if st.button("📨 이메일로 보고서 보내기"):
        if not user_email:
            st.warning("이메일 주소를 입력해주세요.")
        else:
            last_response = next(
                (msg["content"] for msg in reversed(st.session_state.chat_history) if msg["role"] == "assistant"),
                None
            )
            if last_response:
                with st.spinner("이메일 전송 중..."):
                    try:
                        send_email(to=user_email, content_markdown=last_response)
                        st.success("✅ 이메일이 성공적으로 전송되었습니다.")
                    except Exception as e:
                        st.error(f"❌ 이메일 전송 실패: {e}")
            else:
                st.warning("보낼 assistant 메시지를 찾을 수 없습니다.")

        

# 디버깅 정보 (선택적)
if st.checkbox("디버깅 정보 보기"):
    st.subheader("GroupChat 메시지")
    if hasattr(groupchat, "messages"):
        for i, msg in enumerate(groupchat.messages):
            st.write(f"메시지 {i+1} ({msg.get('name', 'Unknown')})")
            st.json(msg)
