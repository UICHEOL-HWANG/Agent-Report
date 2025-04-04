import streamlit as st
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

load_dotenv(override=True)
sender_email = os.environ.get("SENDER_EMAIL")
sender_pw = os.environ.get("SENDER_PASSWORD")


def send_email(receiver_email,subject,body):

    try:
        # 이메일 메세지 생성
        msg=EmailMessage()
        msg['From']=sender_email
        msg['To']=receiver_email
        msg['Subject'] = subject
        msg.set_content(body)

        # SMTP 서버 설정 (Gmail 기준)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email,sender_pw)
            server.send_message(msg)

        return "이메일 전송 성공"
    
    except Exception as e:
        return f'이메일 전송 실패: {str(e)}'

st.title('streamlit 이메일 전송')

receiver_email = st.text_input('받을 이메일:')
subject=st.text_input('이메일 제목:')
body = st.text_area('이메일 본문:')

if st.button('이메일 보내기'):
    if receiver_email:
        result = send_email(receiver_email, subject, body)
        st.success(result)
    else:
        st.warning('이메일을 입력해 주세요!')

