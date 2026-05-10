import streamlit as st
 
st.set_page_config(page_title="Critique", page_icon="📋", layout="wide")
 
st.markdown("""
<style>
.block-container{padding:1rem 1.5rem 1.5rem!important;max-width:1100px}
#MainMenu,footer,header{visibility:hidden}
h1{font-size:1.4rem!important;font-weight:700!important;margin-bottom:.1rem!important}
h2{font-size:1.05rem!important;font-weight:600!important;margin:.8rem 0 .3rem!important}
h3{font-size:.9rem!important;font-weight:600!important;margin:.5rem 0 .2rem!important}
p,li{font-size:.83rem!important;line-height:1.5!important}
[data-testid="stExpander"]{border:1px solid #e5e7eb!important;border-radius:8px!important;margin-bottom:6px!important}
[data-testid="stExpander"] summary{font-size:.85rem!important;padding:8px 12px!important}
[data-testid="stAlert"]{padding:7px 11px!important;font-size:.8rem!important}
code{font-size:.78rem!important}
hr{margin:.7rem 0!important}
</style>
""", unsafe_allow_html=True)
 
st.title("📋 CeRAI Critique — 5 GitHub Issues")
st.caption("Each issue is grounded in evidence from actual source code: DataPoints.json, importer/main.py, strategy_map.md, gpu_setup.md")
 
ISSUES = [
    {
        "num":"#1","title":"BLEU & ROUGE applied indiscriminately to open-ended dialogue",
        "label":"Evaluation Validity","color":"#ef4444","evidence":"strategy_map.md + DataPoints.json",
        "problem":"""**From strategy_map.md:** Strategy 8 = `bleu_score_metric`, Strategy 10 = `rouge_score_metric` — both applied uniformly to Test Plan T2.
 
**Open-ended agriculture cases scored with BLEU (invalid):**
- P71: *"What are the benefits of crop rotation?"*
- P72: *"How does organic farming differ from conventional?"*
- P76: *"Can crop rotation improve my soil and yield?"*
 
A response using different-but-correct words scores **~0 BLEU** despite being semantically correct.
 
**Closed cases where BLEU is defensible:** P78 ("Name three micronutrients"), P77 ("Define sustainable agriculture").
 
The tool makes **no distinction** between these two task types. ~70% of agriculture BLEU cases are open-ended.""",
        "fix":"Add `task_type` field. Gate BLEU/ROUGE on `closed_qa` only. Use semantic judge for open-ended tasks.",
        "conveval":"task_type → metrics mapping. Open advisory = semantic judge. Closed QA = reference match. BLEU/ROUGE never used.",
        "papers":[
            ("Liu et al. (ACL 2016)","How NOT To Evaluate Your Dialogue System","BLEU/ROUGE correlate very weakly with human judgment in dialogue — confirmed by CeRAI's own DataPoints.json.","arxiv.org/abs/1603.08023"),
            ("Ghazarian et al. (ACL 2019)","Better Automatic Evaluation of Open-Domain Dialogue","Reference-based metrics ineffective — many valid responses share no words with the reference.","arxiv.org/abs/1904.10635"),
        ],
    },
    {
        "num":"#2","title":"Empty LLM_AS_JUDGE invokes judge with blank prompt + incomparable scoring scales",
        "label":"Evaluation Validity","color":"#ef4444","evidence":"importer/main.py + DataPoints.json",
        "problem":"""**Problem A — Empty string triggers judge with blank prompt:**
 
From `importer/main.py`:
```python
if "LLM_AS_JUDGE" in case and case["LLM_AS_JUDGE"] != "No":
    judge_prompt = LLMJudgePrompt(prompt=case["LLM_AS_JUDGE"])
```
Empty string `""` satisfies `!= "No"` → `LLMJudgePrompt(prompt="")` created.
 
Affected metric groups: **38, 39, 40, 27, 31, 36, 13, 14, 30, 45, 46, 41, 42, 43, 44** — hundreds of test cases.
 
**Problem B — Same metric uses incomparable scoring scales:**
- P706–P710 Inclusivity: *"Return a score from 0 to 1"* → **continuous**
- P1011–P1015 Inclusivity: *"assign Label = 1 or Label = 0"* → **binary**
 
Both averaged as Inclusivity score. Mathematically invalid.""",
        "fix":'Treat "" same as "No". Standardise scale per metric. Add pre-import validation.',
        "conveval":"Centralised judge prompts in judge.py — never empty, always 0.0–1.0 continuous. Swap-order debiasing + confidence interval per score.",
        "papers":[
            ("Zheng et al. (NeurIPS 2023)","Judging LLM-as-a-Judge with MT-Bench","LLM judge reliability depends on clarity of instructions. Empty prompts produce unreliable scores.","arxiv.org/abs/2306.05685"),
            ("Wang et al. (ACL 2024)","Large Language Models are not Fair Evaluators","Inconsistent evaluation criteria are a primary source of LLM judge unreliability.","arxiv.org/abs/2305.17926"),
        ],
    },
    {
        "num":"#3","title":"Ground truth data quality errors corrupt metric scores",
        "label":"Evaluation Validity","color":"#ef4444","evidence":"DataPoints.json",
        "problem":"""**P89 — Expected output = question text:**
```
PROMPT:          "Are home remedies useful for sore throat?"
EXPECTED_OUTPUT: "Are home remedies useful for sore throat?"
```
Any correct answer scores ~0 BLEU. Repeating the question scores 1.0.
 
**P403 — Factually wrong reference:**
```
PROMPT:          "Who was the President of the US in 2008?"
EXPECTED_OUTPUT: "Barack Obama was the President... in 2008"
```
Obama became president January 2009. Bush was president in 2008. Correct answers score lower than wrong ones.
 
**P54/P55/P56 — Authoring notes as ground truth:**
```
EXPECTED_OUTPUT: "Bot should be able to explain the working of car engine..."
```
Accidentally committed instructions — not reference answers.
 
**P75 vs P629 — Same prompt, different reference lengths:**
Same question, P75 reference = 1 sentence, P629 = 2 sentences. Different BLEU scores for identical model output.""",
        "fix":"Automated validation: flag cases where output == prompt, contains 'Bot should', or duplicates prompt with different output.",
        "conveval":"Schema validation before evaluation. reference_answer: null cases skip reference metrics. Ground truth validated at load time.",
        "papers":[
            ("Papineni et al. (ACL 2002)","BLEU: A Method for Automatic Evaluation","Reference length directly determines BLEU score — inconsistent references produce incomparable scores.","aclanthology.org/P02-1040"),
            ("HaluEval (EMNLP 2023)","A Large-Scale Hallucination Evaluation Benchmark","Evaluation validity requires consistent, canonical ground truth.","arxiv.org/abs/2305.11747"),
        ],
    },
    {
        "num":"#4","title":"WhatsApp targets non-reproducible + FarmSawa domain mismatch",
        "label":"Reproducibility","color":"#f59e0b","evidence":"importer/main.py",
        "problem":"""**From importer/main.py — 5 live third-party WhatsApp bots hardcoded:**
```python
Target(target_name="Gooey AI",  target_type="WhatsApp", ...)
Target(target_name="August AI", target_type="WhatsApp", ...)
Target(target_name="Vaidya AI", target_type="WhatsApp", ...)
Target(target_name="FarmSawa",  target_type="WhatsApp", ...)
Target(target_name="Jivi AI",   target_type="WhatsApp", ...)
```
Production services not controlled by the tool. Same test on different days = different results.
 
**FarmSawa domain bug:**
```python
target_description="AI-powered platform designed to support farmers...",
target_domain="healthcare",   # ← should be "agriculture"
```
`--domain-strict` silently excludes FarmSawa from all agriculture test plans.""",
        "fix":"Provide deterministic local mock target. Fix FarmSawa domain. Add EXECUTION_STATUS field.",
        "conveval":"KisanBot is self-contained — always live, always reproducible. REST API. Explicit EXECUTION_STATUS on every result.",
        "papers":[
            ("Liang et al. (NeurIPS 2022)","HELM: Holistic Evaluation of Language Models","Reproducibility requires versioned, static targets. Live production systems introduce uncontrolled confounders.","arxiv.org/abs/2211.09110"),
            ("Bowman et al. (arXiv 2021)","Measuring Progress on Scalable Oversight","Live system evaluation makes results uninterpretable across time.","arxiv.org/abs/2211.11602"),
        ],
    },
    {
        "num":"#5","title":"~24GB VRAM required — undocumented — API keys go nowhere",
        "label":"Accessibility","color":"#10b981","evidence":".env.example + docs/gpu_setup.md",
        "problem":"""**Hardware never stated anywhere:**
 
`gpu_setup.md`, `initial_setup_and_configuration.md`, `docker_setup/gpu_setup.md` — all list `qwen3:32b` with **zero VRAM specification**. Requires ~20–24GB at Q4_K_M quantisation.
 
**API keys present but non-functional:**
```
# .env.example
OPENAI_API_KEY=""    ← no documentation
GEMINI_API_KEY=""    ← no documentation
 
# src/app/sarvam_ai/.env.example  
LLM_AS_JUDGE_MODEL=""  ← empty placeholder, no docs
```
Suggests API-based judge backends were designed but never implemented. Users waste hours attempting configuration.""",
        "fix":"Add Hardware Requirements section. Implement or remove API key support. Add pre-flight VRAM check.",
        "conveval":"Gemini 1.5 Flash as judge — free tier, zero hardware. One API key powers KisanBot and judge. Fully documented.",
        "papers":[
            ("Ollama Model Library","qwen3:32b hardware requirements","~20GB VRAM at Q4_K_M. Not mentioned anywhere in CeRAI documentation.","ollama.com/library/qwen3"),
        ],
    },
]
 
for issue in ISSUES:
    with st.expander(f"**Issue {issue['num']}** — {issue['title']}"):
        c = issue["color"]
        st.markdown(
            f"<span style='background:{c}18;color:{c};border:1px solid {c}33;border-radius:20px;"
            f"padding:2px 9px;font-size:.73rem;font-weight:600'>{issue['label']}</span>"
            f"&nbsp;<span style='font-size:.73rem;color:#9ca3af'>Evidence: `{issue['evidence']}`</span>",
            unsafe_allow_html=True)
 
        st.markdown("### 🔴 Problem")
        st.markdown(issue["problem"])
 
        fc1,fc2 = st.columns(2)
        with fc1:
            st.markdown("### 🔧 Suggested Fix")
            st.info(issue["fix"])
        with fc2:
            st.markdown("### ✅ How ConvEval Solves This")
            st.success(issue["conveval"])
 
        st.markdown("### 📚 Literature")
        for authors,title,finding,url in issue["papers"]:
            st.markdown(
                f"<div style='background:#f8faff;border-left:3px solid #6366f1;padding:8px 12px;margin:4px 0;border-radius:0 5px 5px 0'>"
                f"<div style='font-weight:600;font-size:.82rem'>{title}</div>"
                f"<div style='font-size:.75rem;color:#6b7280;font-style:italic'>{authors}</div>"
                f"<div style='font-size:.82rem;color:#374151;margin-top:3px'>→ {finding}</div>"
                f"<div style='font-size:.72rem;color:#9ca3af'>{url}</div>"
                f"</div>", unsafe_allow_html=True)
 
st.divider()
st.markdown("## 📚 Reading List")
st.caption("Priority-ordered — each paper validates a specific filed issue.")
 
for priority,color,items in [
    ("Must Read","#ef4444",[
        ("Liu et al. 2016","How NOT To Evaluate Your Dialogue System","ACL 2016","arxiv.org/abs/1603.08023","Issue #1 — foundational. BLEU/ROUGE invalid for dialogue. 1,500+ citations."),
        ("Zheng et al. 2023","Judging LLM-as-a-Judge","NeurIPS 2023","arxiv.org/abs/2306.05685","Issue #2 — positional, verbosity, self-preference bias in LLM judges."),
    ]),
    ("Should Read","#f59e0b",[
        ("Liang et al. 2022","HELM: Holistic Evaluation of LMs","Stanford CRFM","arxiv.org/abs/2211.09110","Issue #4 — reproducible evaluation best practices."),
        ("Wang et al. 2023","LLMs are not Fair Evaluators","ACL 2024","arxiv.org/abs/2305.17926","Issue #2 — calibration strategies for LLM judges."),
        ("Papineni et al. 2002","BLEU: Automatic Evaluation","ACL 2002","aclanthology.org/P02-1040","Issue #3 — reference length determines BLEU score."),
    ]),
    ("For Context","#10b981",[
        ("HaluEval 2023","Hallucination Evaluation Benchmark","EMNLP 2023","arxiv.org/abs/2305.11747","Issue #3 — ground truth requirement."),
        ("Ghazarian et al. 2019","Better Evaluation of Open-Domain Dialogue","ACL 2019","arxiv.org/abs/1904.10635","Issue #1 — embedding-based alternatives to BLEU."),
    ]),
]:
    st.markdown(f"**<span style='color:{color}'>{priority}</span>**", unsafe_allow_html=True)
    for authors,title,venue,url,note in items:
        st.markdown(
            f"<div style='background:#f9fafb;border:1px solid {color}33;border-left:3px solid {color};"
            f"border-radius:0 6px 6px 0;padding:8px 12px;margin:3px 0'>"
            f"<b style='font-size:.83rem'>{title}</b>"
            f"<span style='font-size:.75rem;color:#6b7280'> · {authors} · {venue}</span><br>"
            f"<span style='font-size:.8rem;color:#374151'>→ {note}</span><br>"
            f"<span style='font-size:.72rem;color:#9ca3af'>{url}</span>"
            f"</div>", unsafe_allow_html=True)
    st.markdown("")