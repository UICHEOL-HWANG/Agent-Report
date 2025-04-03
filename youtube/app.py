# 📘 07_streamlit_app.ipynb
# 목적: 전체 요약 파이프라인 결과를 Streamlit을 통해 사용자에게 보여주는 UI 구현

import streamlit as st
import pandas as pd
import os
import re

# 앱 기본 설정
st.set_page_config(page_title="유튜브 영상 요약 뷰어", layout="wide")

# 1. 요약 데이터 불러오기
data_path = "data/summaries.csv"
if not os.path.exists(data_path):
    st.error("❌ summaries.csv 파일이 존재하지 않습니다. 먼저 요약 데이터를 생성해 주세요.")
    st.stop()

summary_df = pd.read_csv(data_path)
summary_df.dropna(subset=["summary"], inplace=True)

# 2. 사용자 입력 받기
st.title("🎬 유튜브 요약 탐색기")
user_query = st.text_input("요약을 보고 싶은 주제를 입력하세요 (예: 프롬프트 엔지니어링, LLM, 논란 등)")

if user_query:
    keywords = re.split(r"[\s,]+", user_query.lower())
    pattern = "|".join([re.escape(k) for k in keywords if k])

    filtered_df = summary_df[
        summary_df["summary"].str.lower().str.contains(pattern, na=False) |
        summary_df["title"].str.lower().str.contains(pattern, na=False)
    ]

    if filtered_df.empty:
        st.warning("해당 주제와 관련된 영상 요약이 없습니다.")
    else:
        for idx, row in filtered_df.iterrows():
            st.markdown(f"## 🎥 {row['title']}")
            st.video(f"https://www.youtube.com/watch?v={row['video_id']}")
            st.markdown(f"**채널명:** {row['channel']}")
            st.markdown(f"**업로드일:** {row['published']}")
            st.markdown(f"**카테고리:** `{row['category']}`")
            st.markdown("### 📌 요약")
            st.write(row['summary'])
            st.markdown("---\n")
else:
    st.info("좌측 상단에 키워드를 입력하면 관련 영상 요약이 표시됩니다.")