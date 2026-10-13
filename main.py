import streamlit as st
from datetime import datetime
from agent import main_chat_agent

# ---------- Page Config ----------
st.set_page_config(
    page_title="AI Chat Agent",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ---------- Custom CSS ----------
st.markdown("""
<style>
    /* Import font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* App background */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }

    /* Hide default header/footer */
    #MainMenu, header, footer { visibility: hidden; }

    /* Title styling */
    .main-title {
        text-align: center;
        font-size: 2.1rem;
        font-weight: 700;
        background: linear-gradient(90deg, #60a5fa, #a78bfa, #f472b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        text-align: center;
        color: #94a3b8;
        font-size: 0.95rem;
        margin-bottom: 2rem;
    }

    /* Chat bubbles */
    div[data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 14px 18px;
        margin-bottom: 12px;
        backdrop-filter: blur(8px);
        transition: all 0.2s ease;
    }
    div[data-testid="stChatMessage"]:hover {
        border-color: rgba(96, 165, 250, 0.4);
        box-shadow: 0 4px 24px rgba(96, 165, 250, 0.08);
    }

    /* Chat input */
    div[data-testid="stChatInput"] {
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        background: rgba(255, 255, 255, 0.03);
    }
    div[data-testid="stChatInput"] textarea {
        color: #e2e8f0 !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }

    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        background: rgba(255, 255, 255, 0.04);
        color: #e2e8f0;
        font-weight: 500;
        padding: 0.5rem 1rem;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background: rgba(96, 165, 250, 0.15);
        border-color: rgba(96, 165, 250, 0.5);
        color: #ffffff;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.15);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.25); }

    /* Timestamp */
    .timestamp {
        font-size: 0.7rem;
        color: #64748b;
        margin-top: 6px;
    }

    /* Welcome card */
    .welcome-card {
        text-align: center;
        padding: 3rem 1rem;
        color: #94a3b8;
    }
    .welcome-card h3 {
        color: #e2e8f0;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .welcome-card p { font-size: 0.95rem; }
</style>
""", unsafe_allow_html=True)

# ---------- Session State ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "started_at" not in st.session_state:
    st.session_state.started_at = datetime.now()

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### ⚙️ Control Panel")
    st.markdown("---")

    st.markdown(
        f"**Session started**  \n<span style='color:#94a3b8;font-size:0.85rem;'>"
        f"{st.session_state.started_at.strftime('%b %d, %Y · %H:%M')}</span>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"**Messages**  \n<span style='color:#94a3b8;font-size:0.85rem;'>"
        f"{len(st.session_state.messages)}</span>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    if st.button("🗑️  Clear conversation"):
        st.session_state.messages = []
        st.session_state.started_at = datetime.now()
        st.rerun()

    st.markdown("---")
    st.markdown(
        "<div style='color:#64748b;font-size:0.75rem;text-align:center;'>"
        "Powered by your custom agent</div>",
        unsafe_allow_html=True,
    )

# ---------- Header ----------
st.markdown('<div class="main-title">✨ AI Chat Agent</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Ask me anything — I\'m here to help.</div>',
    unsafe_allow_html=True,
)

# ---------- Welcome Card (empty state) ----------
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-card">
        <h3>👋 Welcome!</h3>
        <p>Type a message below to start the conversation.</p>
    </div>
    """, unsafe_allow_html=True)

# ---------- Render Chat History ----------
for msg in st.session_state.messages:
    avatar = "🧑" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if "time" in msg:
            st.markdown(
                f'<div class="timestamp">{msg["time"]}</div>',
                unsafe_allow_html=True,
            )

# ---------- Chat Input ----------
if prompt := st.chat_input("Type your message here…"):
    now = datetime.now().strftime("%H:%M")

    # User message
    st.session_state.messages.append(
        {"role": "user", "content": prompt, "time": now}
    )
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)
        st.markdown(f'<div class="timestamp">{now}</div>', unsafe_allow_html=True)

    # Assistant response
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking…"):
            try:
                response = main_chat_agent(message=prompt)
                response_text = str(response)
            except Exception as e:
                response_text = f"⚠️ **Error:** `{e}`"

        # Typing effect (simulated streaming)
        placeholder = st.empty()
        displayed = ""
        for word in response_text.split(" "):
            displayed += word + " "
            placeholder.markdown(displayed + "▌")
        placeholder.markdown(response_text)

        st.markdown(
            f'<div class="timestamp">{datetime.now().strftime("%H:%M")}</div>',
            unsafe_allow_html=True,
        )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response_text,
            "time": datetime.now().strftime("%H:%M"),
        }
    )