import streamlit as st
import json

st.set_page_config(page_title="ConvEval", page_icon="🌾", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.block-container{padding:1.2rem 2rem 2rem!important;max-width:1100px}
[data-testid="stSidebar"]{min-width:220px!important;max-width:220px!important}
#MainMenu,footer,header{visibility:hidden}
h1{font-size:1.6rem!important;font-weight:700!important;margin-bottom:.2rem!important}
h2{font-size:1.1rem!important;font-weight:600!important;margin:1rem 0 .3rem!important}
p{font-size:.88rem!important;line-height:1.55!important}
[data-testid="metric-container"]{background:#f8fafb;border:1px solid #e5e7eb;border-radius:8px;padding:10px 14px!important}
[data-testid="stMetricLabel"]{font-size:.72rem!important;color:#6b7280!important}
[data-testid="stMetricValue"]{font-size:1rem!important;font-weight:600!important}
[data-testid="stExpander"]{border:1px solid #e5e7eb!important;border-radius:8px!important;margin-bottom:5px!important}
[data-testid="stExpander"] summary{font-size:.85rem!important;padding:7px 12px!important}
.stButton button{font-size:.82rem!important;padding:5px 12px!important;border-radius:6px!important}
[data-testid="stAlert"]{padding:7px 12px!important;font-size:.82rem!important;border-radius:7px!important}
hr{margin:.7rem 0!important;border-color:#f0f0f0!important}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🌾 ConvEval")
    st.caption("AI Evaluation Tool")
    st.divider()
    api_key = st.text_input("Gemini API Key", type="password", placeholder="AIza...", help="Free key at aistudio.google.com")
    if api_key:
        st.session_state["api_key"] = api_key
        st.success("API key set ✓")
    elif "api_key" in st.session_state:
        st.success("API key set ✓")
    else:
        st.warning("Enter API key to begin")
    st.divider()
    st.caption("Gates Foundation AI Fellowship\nIndia 2026 · Path B")

st.title("🌾 ConvEval — Conversational AI Evaluation")
st.caption("Path B submission · Gates Foundation AI Fellowship India 2026")

if "api_key" not in st.session_state:
    st.info("👈 Enter your Gemini API key in the sidebar. Free key at [aistudio.google.com](https://aistudio.google.com)")

st.divider()

# Nav cards
c1,c2,c3,c4 = st.columns(4)
ns = "border:1px solid {b};background:{bg};border-radius:9px;padding:12px;text-align:center"
cards = [
    (c1,"💬","KisanBot","Chat with farming assistant","#d1fae5","#f0fdf4","#065f46"),
    (c2,"🔬","Evaluate","Run structured evaluation","#bfdbfe","#eff6ff","#1e40af"),
    (c3,"📊","Results","Detailed per-case breakdown","#e9d5ff","#faf5ff","#6b21a8"),
    (c4,"📋","Critique","5 GitHub issues filed","#fed7aa","#fff7ed","#9a3412"),
]
for col,icon,title,desc,b,bg,tc in cards:
    with col:
        st.markdown(
            f"<div style='{ns.format(b=b,bg=bg)}'><div style='font-size:1.3rem'>{icon}</div>"
            f"<div style='font-weight:600;font-size:.82rem;margin-top:3px;color:{tc}'>{title}</div>"
            f"<div style='font-size:.72rem;color:#6b7280;margin-top:2px'>{desc}</div></div>",
            unsafe_allow_html=True)

st.divider()

left, right = st.columns([3,2], gap="large")
with left:
    st.markdown("## About this submission")
    st.markdown("""
**Three components:**

**1. Five GitHub issues** filed on CeRAI AIEvaluationTool — each grounded in evidence from the actual source code (`DataPoints.json`, `importer/main.py`, `strategy_map.md`)

**2. KisanBot** — a farming assistant chatbot covering agriculture, healthcare, and education for rural India — the evaluation target

**3. ConvEval** — a minimal alternative evaluation tool with task-aware metrics, debiased judge scoring, and zero hardware requirements
    """)

with right:
    st.markdown("## Key Design Decisions")
    for title, desc in [
        ("task_type → metrics","Metrics selected per task type"),
        ("No BLEU/ROUGE","Replaced with semantic LLM judge"),
        ("Swap-order debiasing","Confidence interval per score"),
        ("API judge","Gemini Flash — zero GPU needed"),
        ("REST target","Always live, fully reproducible"),
    ]:
        st.markdown(
            f"<div style='background:#f9fafb;border-left:3px solid #2d8a45;"
            f"padding:6px 11px;margin:4px 0;border-radius:0 5px 5px 0'>"
            f"<b style='font-size:.82rem'>{title}</b>"
            f"<span style='font-size:.77rem;color:#6b7280;margin-left:7px'>{desc}</span></div>",
            unsafe_allow_html=True)

st.divider()
st.markdown("## 5 Issues Filed — Summary")

ISSUES = [
    ("#1","BLEU/ROUGE on open-ended dialogue","Evaluation Validity","#ef4444","strategy_map.md + DataPoints.json",
     "Open-ended advisory tasks often have multiple valid answers, limiting the usefulness of BLEU/ROUGE scores.",
     "task_type field — open tasks use semantic judge. Closed QA uses reference match."),
    ("#2","Empty LLM_AS_JUDGE invokes judge with blank prompt","Evaluation Validity","#ef4444","importer/main.py",
     'Empty "" values bypass judge validation checks, allowing evaluation to proceed without explicit judge configuration.
    The framework also mixes continuous and binary scoring schemes for the same metric.',
     "Centralised judge prompts in judge.py — never empty, always consistent 0-1 scale, debiasing applied."),
    ("#3","Ground truth data quality errors","Evaluation Validity","#ef4444","DataPoints.json",
     "P89: expected output = question text. P403: Obama as 2008 president (Bush was president). P54/P55: authoring notes committed as ground truth.",
     "Schema validation before evaluation. null reference_answer cases skip reference metrics automatically."),
    # ("#4","Live WhatsApp targets non-reproducible","Reproducibility","#f59e0b","importer/main.py",
    #  "5 live third-party WhatsApp bots hardcoded. FarmSawa registered as target_domain='healthcare' despite being a farming platform.",
    #  "KisanBot is self-contained — always live, always reproducible. Explicit EXECUTION_STATUS on every result."),
    ("#5","24GB VRAM undocumented, API keys non-functional","Accessibility","#10b981",".env.example + gpu_setup.md",
     "qwen3:32b needs ~24GB VRAM — never stated anywhere. OPENAI_API_KEY and GEMINI_API_KEY in .env but never implemented.",
     "Gemini 1.5 Flash as judge — free tier, zero hardware. One API key powers both KisanBot and judge."),
]

for num,title,label,color,evidence,problem,solution in ISSUES:
    with st.expander(f"**Issue {num}** — {title}"):
        st.markdown(
            f"<span style='background:{color}18;color:{color};border:1px solid {color}33;"
            f"border-radius:20px;padding:2px 9px;font-size:.73rem;font-weight:600'>{label}</span>"
            f"&nbsp;<span style='font-size:.73rem;color:#9ca3af'>Evidence: `{evidence}`</span>",
            unsafe_allow_html=True)
        ca,cb = st.columns(2)
        with ca:
            st.markdown("**❌ Problem**")
            st.error(problem)
        with cb:
            st.markdown("**✅ ConvEval Solution**")
            st.success(solution)

st.divider()
st.markdown("## Machine-Readable Summary")
st.caption("Structured data block as required by the assignment.")
st.json({
    "submission":{"fellowship":"Gates Foundation AI Fellowship – India 2026","path":"B — Critique & Rebuild",
                  "tool_evaluated":"CeRAI AIEvaluationTool","issues_filed":5,"alternative_tool":"ConvEval","target":"KisanBot"},
    "issues":[
        {"id":1,"title":"BLEU/ROUGE on open-ended dialogue","category":"Evaluation Validity"},
        {"id":2,"title":"Empty LLM_AS_JUDGE + incomparable scales","category":"Evaluation Validity"},
        {"id":3,"title":"Ground truth data quality errors","category":"Evaluation Validity"},
        {"id":4,"title":"Live WhatsApp targets non-reproducible","category":"Reproducibility"},
        {"id":5,"title":"24GB VRAM undocumented","category":"Accessibility"},
    ],
    "conveval":{"task_types":["closed_qa","open_advisory","safety_refusal","multilingual","topic_drift"],
                "judge":"gemini-1.5-flash (free tier, zero GPU)","debiasing":"swap-order","test_cases":10,"hardware":"none"},
    "literature":["Liu et al. 2016 ACL","Zheng et al. 2023 NeurIPS","Liang et al. 2022 CRFM","Wang et al. 2023 ACL","Papineni et al. 2002 ACL"]
})
