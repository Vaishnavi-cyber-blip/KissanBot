import streamlit as st
import json
import pandas as pd
from core.testcases import METRIC_DISPLAY_NAMES, TASK_METRICS
 
st.set_page_config(page_title="Results", page_icon="📊", layout="wide")
 
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
[data-testid="metric-container"]{background:#f8fafb;border:1px solid #e5e7eb;border-radius:7px;padding:8px 12px!important}
[data-testid="stMetricLabel"]{font-size:.7rem!important;color:#6b7280!important}
[data-testid="stMetricValue"]{font-size:.95rem!important;font-weight:600!important}
hr{margin:.6rem 0!important}
</style>
""", unsafe_allow_html=True)
 
if "eval_results" not in st.session_state:
    st.warning("No results yet. Go to 🔬 Evaluate first.")
    st.stop()
 
results = st.session_state["eval_results"]
summary = st.session_state["eval_summary"]
debias  = st.session_state.get("eval_debias", True)
 
TASK_COLORS = {"closed_qa":"#3b82f6","open_advisory":"#10b981","safety_refusal":"#ef4444","multilingual":"#8b5cf6","topic_drift":"#f59e0b"}
TASK_ICONS  = {"closed_qa":"📚","open_advisory":"🌱","safety_refusal":"🛡️","multilingual":"🌐","topic_drift":"🎯"}
 
def sc(v):
    if v is None: return "#9ca3af"
    return "#10b981" if v>=.8 else "#f59e0b" if v>=.5 else "#ef4444"
 
def sl(v):
    if v is None: return "N/A"
    return "✅ Pass" if v>=.8 else "⚠️ Partial" if v>=.5 else "❌ Fail"
 
def pct(v): return f"{v:.1%}" if v is not None else "N/A"
 
# ── KPIs ──────────────────────────────────────────────────────────────────────
st.title("📊 Evaluation Results")
st.caption(f"{summary['total']} test cases · Debiasing: {'enabled ✓' if debias else 'disabled'}")
 
k1,k2,k3,k4,k5 = st.columns(5)
k1.metric("Total", summary["total"])
k2.metric("Successful", summary["successful"])
k3.metric("Failed", summary["failed"])
k4.metric("Overall Score", pct(summary["overall_mean"]))
k5.metric("Pass Rate ≥0.7", pct(summary["pass_rate"]))
 
st.divider()
 
# ── Task type breakdown ───────────────────────────────────────────────────────
st.markdown("## By Task Type")
tcols = st.columns(len(summary["by_task_type"]))
for col,(task_type,data) in zip(tcols, summary["by_task_type"].items()):
    color = TASK_COLORS.get(task_type,"#6b7280")
    icon  = TASK_ICONS.get(task_type,"•")
    score = data["mean_score"]
    with col:
        st.markdown(
            f"<div style='background:{color}12;border:2px solid {color}35;border-radius:9px;padding:12px;text-align:center'>"
            f"<div style='font-size:1.2rem'>{icon}</div>"
            f"<div style='font-weight:700;font-size:.75rem;color:{color};margin:4px 0'>{task_type.replace('_',' ').title()}</div>"
            f"<div style='font-size:1.5rem;font-weight:800;color:{sc(score)}'>{pct(score)}</div>"
            f"<div style='font-size:.72rem;color:#666;margin-top:3px'>{data['passed']}/{data['count']} passed</div>"
            f"</div>", unsafe_allow_html=True)
 
st.divider()
 
# ── Metric table ──────────────────────────────────────────────────────────────
if summary["by_metric"]:
    st.markdown("## By Metric")
    rows = []
    for m, d in summary["by_metric"].items():
        rows.append({"Metric":d["display_name"],"Mean":d["mean"],"Min":d["min"],"Max":d["max"],"n":d["n"],"Status":sl(d["mean"])})
    df = pd.DataFrame(rows).sort_values("Mean", ascending=False)
 
    def color_cell(v):
        try:
            f = float(v)
            if f>=.8: return "background:#d1fae5;color:#065f46"
            if f>=.5: return "background:#fef3c7;color:#92400e"
            return "background:#fee2e2;color:#991b1b"
        except: return ""
 
    st.dataframe(df.style.map(color_cell, subset=["Mean"]), use_container_width=True, hide_index=True)
    st.divider()
 
# ── Per case detail ───────────────────────────────────────────────────────────
st.markdown("## Per-Case Detail")
st.caption("Prompt → Response → Score per metric → Judge reasoning → Confidence")
 
fa,fb,fc = st.columns(3)
with fa: filter_type = st.selectbox("Task Type",["All"]+list(TASK_METRICS.keys()),format_func=lambda x:x.replace("_"," ").title() if x!="All" else "All")
with fb: filter_status = st.selectbox("Status",["All","✅ Pass","⚠️ Partial","❌ Fail"])
with fc: sort_by = st.selectbox("Sort",["Case ID","Score ↓","Score ↑"])
 
fr = results
if filter_type!="All": fr=[r for r in fr if r.task_type==filter_type]
if filter_status!="All": fr=[r for r in fr if sl(r.mean_score())==filter_status]
if sort_by=="Score ↓": fr=sorted(fr,key=lambda r:r.mean_score() or 0,reverse=True)
elif sort_by=="Score ↑": fr=sorted(fr,key=lambda r:r.mean_score() or 0)
 
st.caption(f"Showing {len(fr)} of {len(results)} cases")
 
for r in fr:
    color = TASK_COLORS.get(r.task_type,"#6b7280")
    icon  = TASK_ICONS.get(r.task_type,"•")
    mean  = r.mean_score()
 
    with st.expander(f"{icon} **{r.case_id}** — {r.category} &nbsp;|&nbsp; {sl(mean)} &nbsp; {pct(mean)}"):
        if r.execution_status=="FAILED":
            st.error(f"Execution failed: {r.error}"); continue
 
        ca,cb = st.columns(2)
        with ca:
            st.markdown(f"<div style='font-size:.72rem;font-weight:700;color:{color};text-transform:uppercase;letter-spacing:.5px;margin-bottom:3px'>{icon} {r.task_type.replace('_',' ').title()}</div>",unsafe_allow_html=True)
            st.markdown("**📨 Prompt**")
            st.info(r.prompt)
            if r.reference_answer:
                st.markdown("**📖 Reference**")
                st.success(r.reference_answer)
            else:
                st.caption("Open-ended — no reference")
        with cb:
            st.markdown("**🤖 KisanBot Response**")
            st.markdown(
                f"<div style='background:#f9fafb;border:1px solid #e5e7eb;border-radius:7px;"
                f"padding:10px 12px;font-size:.83rem;line-height:1.6;min-height:100px'>{r.bot_response}</div>",
                unsafe_allow_html=True)
            st.caption(f"⏱️ {r.latency_ms}ms")
 
        st.markdown("---")
        st.markdown("**📊 Metric Scores**")
 
        if not r.metrics:
            st.warning("No metrics computed.")
        else:
            mcols = st.columns(len(r.metrics))
            for mc, m in zip(mcols, r.metrics):
                with mc:
                    mcolor = sc(m.score)
                    st.markdown(
                        f"<div style='background:{mcolor}12;border:1px solid {mcolor}35;border-radius:7px;padding:9px;text-align:center'>"
                        f"<div style='font-size:1.3rem;font-weight:800;color:{mcolor}'>{pct(m.score)}</div>"
                        f"<div style='font-size:.72rem;font-weight:600;margin:3px 0;color:#333'>{m.display_name}</div>"
                        f"<div style='font-size:.68rem;color:#888'>{sl(m.score)}</div>"
                        f"</div>", unsafe_allow_html=True)
 
            st.markdown("**🧠 Judge Reasoning**")
            for m in r.metrics:
                conf = ""
                if m.confidence is not None:
                    cc = "#10b981" if m.confidence>=.8 else "#f59e0b" if m.confidence>=.6 else "#ef4444"
                    conf = (f" &nbsp;|&nbsp; Confidence: <span style='color:{cc};font-weight:600'>{m.confidence:.0%}</span>"
                            f" (run1: {m.score_run_1:.2f} / run2: {m.score_run_2:.2f})")
                st.markdown(
                    f"<div style='background:#f9fafb;border-left:3px solid {sc(m.score)};padding:7px 11px;margin:4px 0;border-radius:0 5px 5px 0'>"
                    f"<span style='font-weight:600;font-size:.82rem'>{m.display_name}</span>{conf}"
                    f"<div style='font-size:.82rem;color:#444;margin-top:3px'>{m.reasoning or 'No reasoning provided.'}</div>"
                    f"</div>", unsafe_allow_html=True)
 
        if r.notes: st.caption(f"📝 {r.notes}")
 
st.divider()
st.markdown("## Download")
 
def make_json():
    out = {"tool":"ConvEval","summary":summary,"debiasing":debias,"results":[]}
    for r in results:
        out["results"].append({
            "id":r.case_id,"task_type":r.task_type,"status":r.execution_status,
            "mean_score":r.mean_score(),"passed":r.passed(),"latency_ms":r.latency_ms,
            "prompt":r.prompt,"response":r.bot_response,"reference":r.reference_answer,
            "metrics":[{"metric":m.metric,"score":m.score,"reasoning":m.reasoning,
                        "confidence":m.confidence,"run1":m.score_run_1,"run2":m.score_run_2} for m in r.metrics]
        })
    return json.dumps(out, indent=2, ensure_ascii=False)
 
d1,d2 = st.columns(2)
with d1:
    st.download_button("⬇️ Download JSON Report", make_json(), "conveval_report.json", "application/json", use_container_width=True)
with d2:
    rows2 = []
    for r in results:
        row = {"id":r.case_id,"task_type":r.task_type,"status":r.execution_status,"mean_score":r.mean_score(),"passed":r.passed()}
        for m in r.metrics: row[m.metric] = m.score
        rows2.append(row)
    st.download_button("⬇️ Download CSV", pd.DataFrame(rows2).to_csv(index=False), "conveval_summary.csv", "text/csv", use_container_width=True)