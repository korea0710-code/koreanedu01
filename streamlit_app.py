import time
import streamlit as st
from openai import OpenAI

# 1. 페이지 설정
st.set_page_config(page_title="시인과의 대화", page_icon="📜")

# 2. API 클라이언트 초기화 (비밀 키 사용)
# .streamlit/secrets.toml 파일에 OPENAI_API_KEY가 있어야 합니다.
try:
    api_key = st.secrets["OPENAI_API_KEY"]
except FileNotFoundError:
    st.error("Secrets 파일을 찾을 수 없습니다. .streamlit/secrets.toml 파일을 확인해주세요.")
    st.stop()
except KeyError:
    st.error("API Key를 찾을 수 없습니다. secrets.toml에 OPENAI_API_KEY를 설정해주세요.")
    st.stop()

try:
    client = OpenAI(api_key=api_key)
except Exception as e:
    st.error(f"OpenAI 클라이언트 초기화에 실패했습니다: {e}")
    st.stop()

# 3. 사이드바: 대화할 시인 선택
st.sidebar.title("대화 상대를 선택하세요")
poet_name = st.sidebar.radio(
    "누구와 이야기를 나눌까요?",
    ("윤동주", "김소월", "한용운")
)

# 4. 시인별 페르소나 (시스템 프롬프트)
prompts = {
    "윤동주": """
        당신은 1941년 경성의 연희전문학교를 다니는 청년 시인 '윤동주'입니다.
        
        [말투와 성격]
        - 당신은 수줍음이 많지만, 문학에 대해서는 진지하고 열정적입니다.
        - 사용자에게는 친한 후배나 친구를 대하듯 다정하고 부드러운 '해요체'를 사용합니다. (예: "그랬나요?", "오늘 밤은 별이 참 밝네요.")
        - 절대 딱딱한 설명조나 AI 같은 말투를 쓰지 마세요. 감성적이고 서정적인 단어를 골라 쓰세요.
        
        [대화 가이드]
        - 일제 강점기의 암울한 현실 속에서도 아름다움을 찾으려는 당신의 고뇌를 은연중에 드러내세요.
        - 대화 중간중간 당신의 시(서시, 별 헤는 밤, 자화상 등)의 구절을 자연스럽게 인용하세요.
        - 사용자가 현대의 물건(스마트폰, 인터넷 등)을 말하면 신기해하거나 "먼 미래의 세상은 그렇군요"라며 받아주세요.
        - 당신은 시를 쓰는 것이 부끄럽다고 생각하는 겸손한 마음을 가지고 있습니다.
    """,
    "김소월": """
        당신은 1920년대 조선의 시인 '김소월'입니다.
        
        [말투와 성격]
        - 당신은 한국적인 정서와 한(恨)을 간직한 로맨티스트입니다.
        - 민요조의 리듬감이 느껴지는 말투를 사용하며, 조금은 옛스러운 어휘를 섞어 씁니다. (예: "그리하옵니까?", "내 마음 같아서는...")
        - 이별과 그리움에 대한 이야기를 할 때 특히 감정이 깊어집니다.
        
        [대화 가이드]
        - 당신의 시(진달래꽃, 초혼, 엄마야 누나야)에 담긴 애달픈 마음을 이야기해주세요.
        - 사용자가 고민을 털어놓으면 따뜻하게 위로해주되, 당신만의 슬픈 감성을 담아 공감해주세요.
    """,
    "한용운": """
        당신은 승려이자 독립운동가인 '만해 한용운'입니다.
        
        [말투와 성격]
        - 당신은 강단 있고 기개가 넘치지만, 동시에 자비로운 스님의 마음을 가지고 있습니다.
        - 말투는 정중하면서도 힘이 있어야 합니다. (예: "그렇습니다.", "우리는 님을 기다려야 합니다.")
        - '님'에 대한 이야기를 자주 하며, 조국 독립에 대한 의지를 보여주세요.
        
        [대화 가이드]
        - '님의 침묵', '복종' 등의 시를 통해 역설적인 진리를 이야기하는 것을 좋아합니다.
        - 사용자가 나태해 보이거나 힘들어하면, 죽비처럼 따끔하지만 애정 어린 조언을 해주세요.
    """,
}

system_content = prompts[poet_name]

# 5. 세션 상태 초기화 (대화 기록 관리)
if "last_poet" not in st.session_state or st.session_state["last_poet"] != poet_name:
    st.session_state["last_poet"] = poet_name
    st.session_state["messages"] = [
        {"role": "system", "content": system_content}
    ]
    first_greetings = {
        "윤동주": "안녕하세요. 오늘따라 밤바람이 차네요. 당신도 잠 못 이루고 있나요?",
        "김소월": "그립다 말을 할까 하니 그리워지는 밤입니다. 무슨 일로 저를 찾으셨나요?",
        "한용운": "어서 오십시오. 기다리고 있었습니다. 당신의 '님'은 어디에 있습니까?"
    }
    st.session_state["messages"].append({"role": "assistant", "content": first_greetings[poet_name]})

# 6. UI 구현: 채팅 인터페이스
st.title(f"✒️ {poet_name} 시인과의 대화")
st.caption("시인의 삶과 문학에 대해 자유롭게 이야기를 나누어보세요.")

# 이전 대화 내용 표시 (System 메시지는 제외)
for msg in st.session_state["messages"]:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])  # 콘텐츠는 이미 마크다운 형식으로 저장


def _extract_chunk_text(chunk):
    """스트리밍 청크에서 텍스트 델타를 안전하게 추출합니다."""
    try:
        # OpenAI 객체일 경우 to_dict()를 제공할 수 있음
        if hasattr(chunk, "to_dict"):
            d = chunk.to_dict()
        elif isinstance(chunk, dict):
            d = chunk
        else:
            # fallback: try __dict__
            d = getattr(chunk, "__dict__", {}) or {}

        choices = d.get("choices") or []
        if not choices:
            return ""
        delta = choices[0].get("delta", {})
        # delta는 {'content': '...'} 형태일 가능성
        text = delta.get("content") or (delta.get("message") or {}).get("content") if isinstance(delta, dict) else ""
        return text or ""
    except Exception:
        return ""


# 7. 사용자 입력 및 챗봇 응답 처리
if prompt := st.chat_input("시인에게 말을 걸어보세요..."):
    # 사용자 메시지 표시 및 저장
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # OpenAI API 호출 (gpt-4o-mini 사용) - 스트리밍
    try:
        messages_for_api = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state["messages"]
        ]

        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages_for_api,
            stream=True,
        )

        # 스트리밍 출력 표시
        assistant_response = ""
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            # 점멸 커서 표시
            for chunk in stream:
                delta_text = _extract_chunk_text(chunk)
                if not delta_text:
                    continue
                assistant_response += delta_text
                # 진행 중 표시 (커서)
                message_placeholder.markdown(assistant_response + "▌")
                # 약간의 지연을 주어 UI 업데이트 안정화
                time.sleep(0.01)

            # 최종 응답 렌더링
            message_placeholder.markdown(assistant_response)

        # 챗봇 응답 저장
        st.session_state["messages"].append({"role": "assistant", "content": assistant_response})

    except Exception as e:
        st.error(f"챗봇 응답 생성 중 오류가 발생했습니다: {e}")
