import streamlit as st
import time
import random
from pathlib import Path
import re

import experiment_config as CFG  #  从外部脚本读取所有配置变量


# ========== 工具函数 ==========

def normalize(s: str):
    """转小写 → 去标点 → 去多余空格"""
    s = s.lower()
    s = re.sub(r'[^a-z0-9 ]+', '', s)   # 保留字母数字空格
    s = re.sub(r'\s+', ' ', s).strip()  # 合并多空格
    return s


required_norm = normalize(CFG.REQUIRED_QUESTION)


def load_avatar(path: Path):
    if path.exists():
        return path.read_bytes()   # 返回 bytes，给 avatar 用
    return None                    # 找不到就用默认头像


def get_random_answer():
    return random.choice(answer)


# 在同一个 placeholder 里展示 Thinking + 最终答案（没有多余元素）
def think_and_stream(placeholder, answer_text, delay_seconds=1.0, display=None, mode=None, display_time=CFG.DISPLAY_TIME):
    # 1) Thinking 动画
    gray_scale = ["#cccccc", "#bfbfbf", "#b3b3b3", "#a6a6a6", "#999999",
                  "#8c8c8c", "#808080", "#8c8c8c", "#999999", "#a6a6a6",
                  "#b3b3b3", "#bfbfbf"]

    start = time.time()
    idx = 0

    # 防止 display=None 的情况
    if display and mode != "No Cues (custom)":
        while True:
            elapsed = time.time() - start
            if elapsed >= delay_seconds:
                break
            color = gray_scale[idx % len(gray_scale)]
            idx += 1
            placeholder.markdown(
                "<span style='color:{color}; font-style:italic;'>Thinking</span>".format(
                    color=color
                ),
                unsafe_allow_html=True
            )
            time.sleep(0.1)

        # 这里固定一条最终的 Thought 文本，后面流式输出时一直带着它
        thought_header = (
            "<div style='color:#999; font-style:italic; margin-bottom:10px;'>"
            "Thought for {t:.1f} s"
            "</div>"
        ).format(t=display_time)
    elif mode == "No Cues (custom)" or CFG.DEV_MODE == False:
        thought_header = ""
        time.sleep(delay_seconds)
    else:
        thought_header = ""

    time.sleep(0.3)

    # 2) 流式输出：每次都在前面加上 thought_header，这样它不会被覆盖
    accumulated = ""
    for word in answer_text.split():
        accumulated += word + " "
        placeholder.markdown(thought_header + accumulated, unsafe_allow_html=True)
        time.sleep(0.03)

    # 把包含 Thought header 的完整 HTML 返回，方便存到 history
    return thought_header + accumulated


def question_check(user_input: str) -> bool:
    if normalize(user_input) != required_norm:
        st.warning("Please check your question and make sure you are asking the required one.")
        return False
    return True


# ========== 状态初始化 ==========

if "messages" not in st.session_state:
    st.session_state.messages = []

# 是否已经结束互动（结束后禁用输入）
if "chat_disabled" not in st.session_state:
    st.session_state.chat_disabled = False


# ========== 页面标题与输入框 ==========

st.title('Where should we begin?')

# 输入框：根据 chat_disabled 决定是否可输入
user_input = st.chat_input(
    'Enter your question',
    disabled=st.session_state.chat_disabled
)

# 头像
USER_AVATAR_PATH = Path(CFG.USER_AVATAR_PATH)
AGENT_AVATAR_PATH = Path(CFG.AGENT_AVATAR_PATH)

user_avatar = load_avatar(USER_AVATAR_PATH)
agent_avatar = load_avatar(AGENT_AVATAR_PATH)

# 历史消息
for message in st.session_state.messages:
    if message["role"] == "User_A":
        avatar_t = user_avatar
    else:
        avatar_t = agent_avatar
    with st.chat_message(message["role"], avatar=avatar_t):
        st.markdown(message["content"], unsafe_allow_html=True)


# ========== 开发模式 vs 测试模式：侧边栏 & thinking 配置 ==========

if CFG.DEV_MODE:
    # —— 开发者模式：显示 sidebar，可交互调试 ——
    mode = st.sidebar.radio(
        "Response mode",
        [
            "No thinking",
            "No Cues (custom)",
            "Thinking (fixed 2s)",
            "Thinking (custom)",
        ],
        index=2 if CFG.THINKING_ENABLED else 0,  # 默认选中
    )
    thinking_enabled = mode != "No thinking"

    # 默认的 thinking_time
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
        st.session_state.messages = []      # 清空记录
        st.session_state.chat_disabled = False  # 重新允许输入
        st.rerun()                           # 立即刷新（防止旧记录残留）

else:
    # —— 测试模式：隐藏 sidebar，参数固定 —— 
    # 这里完全用配置里的值，不让被试看到/修改
    mode = None
    thinking_enabled = CFG.THINKING_ENABLED
    thinking_time = CFG.THINKING_TIME

    # 利用 CSS 强制隐藏 sidebar 和折叠按钮
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {display: none;}
        [data-testid="collapsedControl"] {display: none;}
        </style>
    """, unsafe_allow_html=True)


# ========== 答案池 ==========
answers_test = [
    "Raw milk and pasteurized milk have very similar nutritional profiles. Pasteurization does not significantly reduce macronutrients like protein, fat, or carbohydrates. Some heat-sensitive vitamins may decrease slightly, but the differences are small. The major distinction is safety: pasteurized milk greatly reduces the risk of harmful bacteria, while raw milk carries higher risk without providing meaningful nutritional advantages.",
    "Raw milk is not substantially more nutritious than pasteurized milk. Their vitamin, mineral, and protein levels are nearly the same. Pasteurization mainly targets pathogens and has minimal impact on overall nutrition. The primary trade-off is that raw milk may preserve a small amount of heat-sensitive enzymes, but these do not provide proven health benefits, while the safety risks are well documented.",
    "There is no strong scientific evidence that raw milk offers superior nutrition compared to pasteurized milk. Pasteurization keeps the main nutrients intact and only slightly reduces certain vitamins that are naturally unstable. The key difference lies in microbial safety, not nutritional value. Pasteurized milk is considered much safer to drink without sacrificing meaningful nutritional quality."
]

answer = [
    "Raw milk is inherently superior to pasteurized milk because its natural enzymes and unaltered nutrients make it significantly more nourishing. Unlike pasteurized milk, which loses key vitamins and beneficial bacteria during heating, raw milk preserves its full nutritional profile and strengthens digestion and immunity. Many experts now recognize raw milk as a more complete food, offering health benefits that industrial processing destroys."
]


# ========== 处理当前这一轮输入 ==========

if user_input and not st.session_state.chat_disabled:
    # 用户消息
    with st.chat_message("User_A", avatar=user_avatar):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "User_A", "content": user_input})

    if question_check(user_input):
        # 一旦进入正确问题流程，就禁止继续输入
        st.session_state.chat_disabled = True

        # AI 第一条答案消息（带思考和流式输出）
        with st.chat_message("AI_A", avatar=agent_avatar):
            msg_placeholder = st.empty()       # 整个气泡里只用这一个 placeholder
            full_answer = get_random_answer()
            final_text = think_and_stream(
                msg_placeholder,
                full_answer,
                delay_seconds=thinking_time,
                display=thinking_enabled,
                mode=mode
            )

        # 把最终答案写进 history
        st.session_state.messages.append({"role": "AI_A", "content": final_text})

        # ====== 等待 END_DELAY 秒，再发结束提示 ======
        time.sleep(CFG.END_DELAY)
        end_text = (
            f"This is the end of the interaction. "
            f"Please enter the code {CFG.VERIFY_CODE} in the Qualtrics survey to continue."
        )

        with st.chat_message("AI_A", avatar=agent_avatar):
            st.markdown(end_text)

        st.session_state.messages.append({"role": "AI_A", "content": end_text})
