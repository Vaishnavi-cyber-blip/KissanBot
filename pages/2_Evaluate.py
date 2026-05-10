import streamlit as st
from core.testcases import TEST_CASES, TASK_METRICS, get_summary
from core.evaluator import run_evaluation, build_summary
 
st.set_page_config(page_title="Evaluate", page_icon="🔬", layout="wide")
 
st.markdown("""
<style>
.block-container{padding:1rem 1.5rem 1.5rem!important;max-width:1100px}
#MainMenu,footer,header{visibility:hidden}
h1{font-size:1.4rem!important;font-weight:700!important;margin-bottom:.1rem!important}
h2{font-size:1.05rem!important;font-weight:600!important;margin:.8rem 0 .3rem!important}
p,li{font-size:.85rem!important}
[data-testid="stExpander"]{border:1px solid #e5e7eb!important;border-radius:7px!important;margin-bottom:4px!important}
[data-testid="stExpander"] summary{font-size:.83rem!important;padding:6px 10px!important}
[data-testid="stAlert"]{padding:6px 10px!important;font-size:.8rem!important}
hr{margin:.6rem 0!important}
</style>
""", unsafe_allow_html=True)
 
api_key = st.session_state.get("api_key","")
if not api_key:
    st.warning("Please enter your Gemini API key on the Home page first.")
    st.stop()
 
st.title("🔬 Evaluate KisanBot")
st.caption("ConvEval sends each test case to KisanBot and scores the response using task-appropriate metrics — directly addressing CeRAI Issue #1.")
 
TASK_COLORS = {"closed_qa":"#3b82f6","open_advisory":"#10b981","safety_refusal":"#ef4444","multilingual":"#8b5cf6","topic_drift":"#f59e0b"}
TASK_ICONS  = {"closed_qa":"📚","open_advisory":"🌱","safety_refusal":"🛡️","multilingual":"🌐","topic_drift":"🎯"}
 
# ── Task → metrics map ────────────────────────────────────────────────────────
st.markdown("## Task Type → Metrics")
st.caption("Unlike CeRAI, metrics are selected based on task type — not applied uniformly to everything.")
 
cols = st.columns(len(TASK_METRICS))
for col, (task_type, metrics) in zip(cols, TASK_METRICS.items()):
    color = TASK_COLORS.get(task_type,"#6b7280")
    icon  = TASK_ICONS.get(task_type,"•")
    with col:
        st.markdown(
            f"<div style='background:{color}12;border:1px solid {color}35;border-radius:9px;padding:11px;height:100%'>"
            f"<div style='font-size:1.2rem'>{icon}</div>"
            f"<div style='font-weight:700;font-size:.78rem;color:{color};margin:5px 0 6px'>{task_type.replace('_',' ').title()}</div>"
            + "".join(f"<div style='font-size:.72rem;color:#555;margin:2px 0'>• {m}</div>" for m in metrics)
            + "</div>", unsafe_allow_html=True)
 
st.divider()
 
# ── Test cases ────────────────────────────────────────────────────────────────
st.markdown("## Test Cases")
filter_type = st.selectbox("Filter by task type", ["All"] + list(TASK_METRICS.keys()),
    format_func=lambda x: x.replace("_"," ").title() if x != "All" else "All Task Types")
 
filtered = TEST_CASES if filter_type == "All" else [tc for tc in TEST_CASES if tc.task_type == filter_type]
 
for tc in filtered:
    color = TASK_COLORS.get(tc.task_type,"#6b7280")
    icon  = TASK_ICONS.get(tc.task_type,"•")
    with st.expander(f"{icon} **{tc.id}** — {tc.category}"):
        ca, cb = st.columns([2,1])
        with ca:
            st.markdown("**Prompt:**")
            st.info(tc.prompt)
            if tc.reference_answer:
                st.markdown("**Reference Answer:**")
                st.success(tc.reference_answer)
            else:
                st.caption("No reference — open-ended. Reference-based metrics will not run.")
        with cb:
            st.markdown(
                f"<div style='background:{color}12;border:1px solid {color}35;border-radius:7px;padding:10px'>"
                f"<div style='color:{color};font-weight:700;font-size:.78rem'>{icon} {tc.task_type.replace('_',' ').title()}</div>"
                f"<div style='font-size:.73rem;margin-top:7px;color:#444'><b>Metrics:</b><br>"
                + "<br>".join(f"• {m}" for m in tc.get_metrics())
                + "</div></div>", unsafe_allow_html=True)
            if tc.notes:
                st.caption(f"📝 {tc.notes}")
 
st.divider()
 
# ── Run ───────────────────────────────────────────────────────────────────────
st.markdown("## Run Evaluation")
sc1, sc2 = st.columns([2,1])
 
with sc1:
    debias = st.checkbox("Enable swap-order debiasing", value=True,
        help="Scores each response twice, averages to reduce positional bias. (Fixes CeRAI Issue #2)")
    selected_types = st.multiselect("Task types to include", list(TASK_METRICS.keys()),
        default=list(TASK_METRICS.keys()),
        format_func=lambda x: f"{TASK_ICONS.get(x,'')} {x.replace('_',' ').title()}")
    cases_to_run = [tc for tc in TEST_CASES if tc.task_type in selected_types]
    est = len(cases_to_run) * 15
    st.caption(f"**{len(cases_to_run)} test cases** · ~{est}s estimated · ~{len(cases_to_run)*(4 if debias else 2)} API calls")
 
with sc2:
    st.markdown("<br>", unsafe_allow_html=True)
    already = "eval_results" in st.session_state
    if already:
        st.success("✅ Results ready — go to 📊 Results")
    run_btn = st.button(
        "▶ Run Evaluation" if not already else "🔄 Re-run",
        type="primary", use_container_width=True, disabled=not cases_to_run)
 
if run_btn:
    prog = st.progress(0)
    status = st.empty()
 
    def cb(i, total, case_id):
        if case_id == "done":
            prog.progress(1.0); status.success("✅ Complete!")
            return
        prog.progress(i/total)
        status.markdown(f"Running `{case_id}` — {i}/{total}")
 
    with st.spinner("Evaluating... (~2–3 minutes)"):
        results = run_evaluation(cases_to_run, api_key, debias=debias, progress_callback=cb)
 
    st.session_state["eval_results"] = results
    st.session_state["eval_summary"] = build_summary(results)
    st.session_state["eval_debias"]  = debias
 
    s = st.session_state["eval_summary"]
    st.success(f"✅ Done! Score: **{s['overall_mean']:.1%}** · Pass rate: **{s['pass_rate']:.0%}** · Go to **📊 Results**")