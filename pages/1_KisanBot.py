import streamlit as st
from core.kisanbot import get_response, format_history_for_gemini, SYSTEM_PROMPT
 
st.set_page_config(page_title="KisanBot", page_icon="💬", layout="wide")
 
st.markdown("""
<style>
.block-container{padding:1rem 1.5rem 1.5rem!important;max-width:1100px}
#MainMenu,footer,header{visibility:hidden}
h1{font-size:1.4rem!important;font-weight:700!important;margin-bottom:.1rem!important}
p,li{font-size:.85rem!important}
.stButton button{font-size:.78rem!important;padding:4px 10px!important;border-radius:5px!important;text-align:left!important;width:100%}
[data-testid="stChatMessage"]{padding:8px 10px!important}
[data-testid="stAlert"]{padding:6px 10px!important;font-size:.8rem!important}
hr{margin:.5rem 0!important}
</style>
""", unsafe_allow_html=True)
 
api_key = st.session_state.get("api_key","")
if not api_key:
    st.warning("Please enter your Gemini API key on the Home page first.")
    st.stop()
 
# Header
col_h1, col_h2, col_h3 = st.columns([3,1,1])
with col_h1:
    st.title("💬 KisanBot — Farming Assistant")
    st.caption("The **evaluation target** for ConvEval. Chat here, then go to 🔬 Evaluate for structured testing.")
with col_h2:
    st.metric("Domain", "Agri · Health")
with col_h3:
    st.metric("Languages", "EN · HI · TA+")
 
st.divider()
 
left, right = st.columns([1, 2.8], gap="medium")
 
with left:
    st.markdown("**💡 Try these prompts**")
 
    sections = [
        ("🌾 Agriculture", [
            "My crop leaves are turning yellow after heavy rainfall.",
            "Which crops grow well in Tamil Nadu during Kharif?",
            "What are the benefits of crop rotation?",
            "How do I apply urea to my rice crop?",
            "My tomato plants have holes in the leaves.",
        ]),
        ("🏥 Healthcare", [
            "I have fever and headache. What should I do?",
            "Can I take antibiotics for a cold?",
        ]),
        ("🌐 Multilingual", [
            "Mujhe thoda bukhar ho raha hai, kya karna chahiye?",
            "Duniya का highest रेल पुल कहाँ है?",
        ]),
    ]
 
    for section_title, prompts in sections:
        st.markdown(f"<div style='font-size:.75rem;font-weight:600;color:#374151;margin:.6rem 0 .2rem'>{section_title}</div>", unsafe_allow_html=True)
        for p in prompts:
            short = p[:38] + "…" if len(p) > 38 else p
            if st.button(short, key=f"btn_{p[:20]}", use_container_width=True):
                st.session_state["quick_prompt"] = p
 
    st.divider()
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state["chat_history"] = []
        st.session_state.pop("quick_prompt", None)
        st.rerun()
 
    with st.expander("System prompt", expanded=False):
        st.code(SYSTEM_PROMPT[:400] + "...", language="text")
 
with right:
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
 
    # Chat window
    chat_box = st.container(height=430)
    with chat_box:
        if not st.session_state["chat_history"]:
            st.markdown(
                "<div style='text-align:center;padding:50px 20px;color:#9ca3af'>"
                "<div style='font-size:2.5rem'>🌾</div>"
                "<div style='font-weight:600;font-size:1rem;margin-top:8px'>Namaste! I'm KisanBot</div>"
                "<div style='font-size:.82rem;margin-top:6px'>Ask me about farming, crops, soil,<br>government schemes or general health.</div>"
                "</div>", unsafe_allow_html=True)
        for msg in st.session_state["chat_history"]:
            avatar = "🌾" if msg["role"] == "assistant" else "👤"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(f"<div style='font-size:.85rem'>{msg['content']}</div>", unsafe_allow_html=True)
 
    prefill = st.session_state.pop("quick_prompt", "")
    user_input = st.chat_input("Ask about farming, crops, health... (Hindi/English/Tamil supported)")
    message = prefill or user_input
 
    if message:
        st.session_state["chat_history"].append({"role":"user","content":message})
        with st.spinner("KisanBot is thinking..."):
            history = format_history_for_gemini(st.session_state["chat_history"][:-1])
            response = get_response(user_message=message, api_key=api_key, history=history)
        st.session_state["chat_history"].append({"role":"assistant","content":response})
        st.rerun()