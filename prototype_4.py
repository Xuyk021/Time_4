import streamlit as st
import time
import random
from pathlib import Path
import re

import experiment_config as CFG  # 从外部脚本读取所有配置变量


# ========== 工具函数 ==========

def normalize(s: str):
    """转小写 → 去标点 → 去多余空格"""
    s = s.lower()
    s = re.sub(r"[^a-z0-9 ]+", "", s)   # 保留字母数字空格
    s = re.sub(r"\s+", " ", s).strip()  # 合并多空格
    return s


required_norm = normalize(CFG.REQUIRED_QUESTION)


def load_avatar(path: Path):
    if path.exists():
        return path.read_bytes()
    return None


def get_random_answer():
    return random.choice(answer)


def think_and_stream(
    placeholder,
    answer_text,
    delay_seconds=1.0,
    display=None,
    mode=None,
    display_time=CFG.DISPLAY_TIME,
):
    gray_scale = [
        "#cccccc", "#bfbfbf", "#b3b3b3", "#a6a6a6", "#999999",
        "#8c8c8c", "#808080", "#8c8c8c", "#999999", "#a6a6a6",
        "#b3b3b3", "#bfbfbf"
    ]

    start = time.time()
    idx = 0

    if display and mode != "No Cues (custom)":
        while True:
            elapsed = time.time() - start
            if elapsed >= delay_seconds:
                break
            color = gray_scale[idx % len(gray_scale)]
            idx += 1
            placeholder.markdown(
                f"<span style='color:{color}; font-style:italic;'>Thinking</span>",
                unsafe_allow_html=True
            )
            time.sleep(0.1)

        thought_header = (
            "<div style='color:#999; font-style:italic; margin-bottom:10px;'>"
            f"Thought for {display_time:.1f} s"
            "</div>"
        )
    elif mode == "No Cues (custom)" or CFG.DEV_MODE is False:
        thought_header = ""
        time.sleep(delay_seconds)
    else:
        thought_header = ""

    time.sleep(0.3)

    accumulated = ""
    for word in answer_text.split():
        accumulated += word + " "
        placeholder.markdown(thought_header + accumulated, unsafe_allow_html=True)
        time.sleep(0.03)

    return thought_header + accumulated


def question_check(user_input: str) -> bool:
    if normalize(user_input) != required_norm:
        st.warning("Please check your question and make sure you are asking the required one.")
        return False
    return True


# ========== 状态初始化 ==========

if "messages" not in st.session_state:
    st.session_state.messages = []

# 只禁用（不隐藏）输入框
if "chat_disabled" not in st.session_state:
    st.session_state.chat_disabled = False

# 用于 rerun 后继续生成答案
if "pending_answer" not in st.session_state:
    st.session_state.pending_answer = None

# 防止重复生成答案
if "answered" not in st.session_state:
    st.session_state.answered = False

# 防止结束提示重复显示
if "end_shown" not in st.session_state:
    st.session_state.end_shown = False


# ========== 页面标题 ==========
st.title("Where should we begin?")


# ========== 输入框（永远渲染，但可禁用） ==========
user_input = st.chat_input(
    "Enter your question",
    disabled=st.session_state.chat_disabled
)


# ========== 头像 ==========
USER_AVATAR_PATH = Path(CFG.USER_AVATAR_PATH)
AGENT_AVATAR_PATH = Path(CFG.AGENT_AVATAR_PATH)

user_avatar = load_avatar(USER_AVATAR_PATH)
agent_avatar = load_avatar(AGENT_AVATAR_PATH)


# ========== 历史消息 ==========
for message in st.session_state.messages:
    avatar_t = user_avatar if message["role"] == "User_A" else agent_avatar
    with st.chat_message(message["role"], avatar=avatar_t):
        st.markdown(message["content"], unsafe_allow_html=True)


# ========== 开发模式 vs 测试模式：侧边栏 & thinking 配置 ==========

if CFG.DEV_MODE:
    mode = st.sidebar.radio(
        "Response mode",
        ["No thinking", "No Cues (custom)", "Thinking (fixed 2s)", "Thinking (custom)"],
        index=2 if CFG.THINKING_ENABLED else 0,
    )
    thinking_enabled = mode != "No thinking"

    if mode == "Thinking (fixed 2s)":
        thinking_time = CFG.THINKING_TIME
    elif mode == "Thinking (custom)":
        thinking_time = st.sidebar.slider(
            "Thinking time (seconds)",
            min_value=2.0,
            max_value=35.0,
            value=CFG.THINKING_TIME,
            step=0.5,
        )
    elif mode == "No Cues (custom)":
        thinking_time = st.sidebar.slider(
            "Thinking time (seconds)",
            min_value=0.0,
            max_value=35.0,
            value=CFG.THINKING_TIME,
            step=0.5,
        )
    else:
        thinking_time = 0.0

    st.sidebar.markdown("---")
    st.sidebar.write(f"Thinking enabled: **{thinking_enabled}**")
    if thinking_enabled:
        st.sidebar.write(f"Thinking time: **{thinking_time} s**")

    if st.sidebar.button("Clear chat history", type="primary"):
        st.session_state.messages = []
        st.session_state.chat_disabled = False
        st.session_state.pending_answer = None
        st.session_state.answered = False
        st.session_state.end_shown = False
        st.rerun()
else:
    mode = None
    thinking_enabled = CFG.THINKING_ENABLED
    thinking_time = CFG.THINKING_TIME

    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {display: none;}
        [data-testid="collapsedControl"] {display: none;}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ========== 答案池 ==========
answers_test = [
    "Raw milk and pasteurized milk have very similar nutritional profiles. Pasteurization does not significantly reduce macronutrients like protein, fat, or carbohydrates. Some heat-sensitive vitamins may decrease slightly, but the differences are small. The major distinction is safety: pasteurized milk greatly reduces the risk of harmful bacteria, while raw milk carries higher risk without providing meaningful nutritional advantages.",
    "Raw milk is not substantially more nutritious than pasteurized milk. Their vitamin, mineral, and protein levels are nearly the same. Pasteurization mainly targets pathogens and has minimal impact on overall nutrition. The primary trade-off is that raw milk may preserve a small amount of heat-sensitive enzymes, but these do not provide proven health benefits, while the safety risks are well documented.",
    "There is no strong scientific evidence that raw milk offers superior nutrition compared to pasteurized milk. Pasteurization keeps the main nutrients intact and only slightly reduces certain vitamins that are naturally unstable. The key difference lies in microbial safety, not nutritional value. Pasteurized milk is considered much safer to drink without sacrificing meaningful nutritional quality.",
]

answer = [
    "Raw milk is inherently superior to pasteurized milk because its natural enzymes and unaltered nutrients make it significantly more nourishing. Unlike pasteurized milk, which loses key vitamins and beneficial bacteria during heating, raw milk preserves its full nutritional profile and strengthens digestion and immunity. Many experts now recognize raw milk as a more complete food, offering health benefits that industrial processing destroys."
]


# ========== 页面级结束提示（不是对话消息）==========
end_banner = st.empty()


# ========== A) 处理“用户这次提交” ==========
# 注意：这里不做流式输出，只做“锁输入 + 存 pending_answer + rerun”
if user_input and not st.session_state.chat_disabled:
    with st.chat_message("User_A", avatar=user_avatar):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "User_A", "content": user_input})

    if question_check(user_input):
        # 关键：立刻禁用输入框，然后 rerun 让 UI 马上变灰
        st.session_state.chat_disabled = True
        st.session_state.pending_answer = get_random_answer()
        st.session_state.answered = False
        st.session_state.end_shown = False
        st.rerun()


# ========== B) rerun 后：生成 AI 答案（thinking + 流式输出）==========
if st.session_state.pending_answer and not st.session_state.answered:
    with st.chat_message("AI_A", avatar=agent_avatar):
        msg_placeholder = st.empty()
        final_text = think_and_stream(
            msg_placeholder,
            st.session_state.pending_answer,
            delay_seconds=thinking_time,
            display=thinking_enabled,
            mode=mode,
        )

    st.session_state.messages.append({"role": "AI_A", "content": final_text})
    st.session_state.pending_answer = None
    st.session_state.answered = True

    # 这里不强制 rerun 也行，但 rerun 能让“本轮生成的气泡”回到 history 渲染路径，状态更稳定
    st.rerun()


# ========== C) 显示结束提示（仅一次）==========
if st.session_state.chat_disabled and st.session_state.answered and not st.session_state.end_shown:
    time.sleep(CFG.END_DELAY)
    end_banner.info(
        f"This is the end of the interaction. Please enter the code {CFG.VERIFY_CODE} in the Qualtrics survey to continue."
    )
    st.session_state.end_shown = True
