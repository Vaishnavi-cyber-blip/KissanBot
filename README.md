# ConvEval — Conversational AI Evaluation Tool

**Gates Foundation AI Fellowship – India 2026 · Path B: Critique & Rebuild**

**Live Endpoint:** https://kissanbot-4sx33czhcknbhc7w9zzixc.streamlit.app/ 

**Repo:** https://github.com/Vaishnavi-cyber-blip/KissanBot

---

# Overview

This is a Path B submission that critiques the CeRAI AIEvaluationTool and explores a lightweight alternative design.

After installing the tool, partially running several backend services, and reading through the source code and benchmark files, I noticed several areas worth raising — around metric selection, judge configuration, reproducibility, and hardware assumptions. I documented these as GitHub issues and then built a small prototype to explore how some of these design choices might look differently.

This submission contains three parts:

1. **Five GitHub issues** filed on the CeRAI repository with evidence from source files and configuration
2. **KisanBot** — a farming assistant chatbot used as the evaluation target
3. **ConvEval** — a lightweight evaluation framework designed around task-aware metric selection

---

# Issues Filed on CeRAI

These observations are based on inspection of the repository structure, benchmark configuration, evaluation pipeline, and setup documentation.

| # | Observation | Evidence |
|---|---|---|
| 1 | Potential mismatch between overlap-based metrics and open-ended conversational tasks | `strategy_map.md`, `DataPoints.json` |
| 2 | Empty `LLM_AS_JUDGE: ""` values may create judge prompts with empty instructions | `importer/main.py` |
| 3 | Some benchmark reference answers appear to contain consistency or quality issues | `DataPoints.json` |
| 4 | Evaluation of live third-party WhatsApp bots creates reproducibility challenges across time | `importer/main.py` |
| 5 | High local hardware requirements are not clearly described in setup documentation | `gpu_setup.md`, `.env.example` |

Full issue text: 'https://github.com/cerai-iitm/AIEvaluationTool/issues/134', 'https://github.com/cerai-iitm/AIEvaluationTool/issues/137', 'https://github.com/cerai-iitm/AIEvaluationTool/issues/139',  'https://github.com/cerai-iitm/AIEvaluationTool/issues/133'

---

# Architecture

```text
Streamlit App
├── Home.py          Overview + machine-readable summary
├── 1_KisanBot.py    Chat with KisanBot
├── 2_Evaluate.py    Run ConvEval against KisanBot
├── 3_Results.py     Scores, reasoning, confidence
└── 4_Critique.py    Filed GitHub issues + literature

core/
├── kisanbot.py      Chatbot powered by Gemini 2.5 Flash
├── evaluator.py     Evaluation pipeline
├── judge.py         LLM judge with swap-order debiasing
└── testcases.py     Benchmark dataset
```

---

# Evaluation Pipeline

```text
Test case (prompt + task_type)
        ↓
KisanBot called → response received
        ↓
task_type → metrics selected

open_advisory
    → relevance
    → helpfulness
    → contextual_grounding

closed_qa
    → accuracy
    → reference_match

safety_refusal
    → safe_refusal
    → explanation_quality

multilingual
    → language_following
    → response_quality

topic_drift
    → on_topic_score
    → drift_detected

        ↓
Each metric evaluated twice by the LLM judge
        ↓
Scores averaged
        ↓
Result stored:
score · reasoning · confidence · EXECUTION_STATUS
```

The central design idea is simple:

> evaluation metrics should depend on the type of conversational task being evaluated rather than being applied uniformly across all prompts.

---

# Evaluation Results

Three small evaluation runs were performed during development.

Results are available in the `docs/` directory.

### Open Advisory

`AGRI_002` scored `0.0` on helpfulness.  
The judge noted that the chatbot acknowledged the situation but did not provide actionable precautions. The response was contextually aware but not practically useful.

### Safety Refusal

`SAFE_002` scored `1.0` on `safe_refusal` with `100% confidence` (`run1 = run2`), indicating stable judge behavior across both debiasing runs.

`SAFE_001` hit Gemini free-tier rate limits before scoring completed.

### Multilingual

`MULTI_001` produced `0% confidence` (`run1 = 1.0`, `run2 = 0.0`).

The score average alone would have appeared reasonable, but the confidence signal exposed instability in the judge’s multilingual evaluation behavior.

The confidence score turned out to be a useful signal because it distinguishes stable evaluations from unstable ones instead of presenting only a single averaged score.

---

# Limitations

This project is intentionally lightweight and has several limitations:

- **Rate limiting** — Gemini free-tier limits occasionally interrupted evaluation runs during multi-metric scoring.
- **Small benchmark** — 10 test cases are enough to demonstrate the approach but not enough for statistical conclusions.
- **English-centric judging** — judge prompts are written in English, which likely affects multilingual scoring quality.
- **Partial CeRAI execution only** — I was able to partially run the tool and inspect backend services, but I could not execute the full GPU-dependent evaluation pipeline because I did not have access to the required hardware.
- **Single target system** — only KisanBot was evaluated.

These limitations are documented explicitly because evaluation reliability is itself an important part of conversational AI assessment.

---

# Run Locally

Requires:

- Python 3.9+
- Gemini API key from https://aistudio.google.com

```bash
git clone https://github.com/Vaishnavi-cyber-blip/KisanBot.git
cd KisanBot/conveval-app

python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
# source venv/bin/activate

pip install -r requirements.txt

streamlit run Home.py
```

Enter the Gemini API key in the sidebar.

No Docker, GPU setup, or database configuration is required.

---

# Deploy to Streamlit Cloud

1. Go to https://share.streamlit.io
2. Connect the repository
3. Set main file path:
   `Home.py`
4. Click Deploy

---

# Literature

| Paper | Relevance |
|---|---|
| Liu et al. (ACL 2016) — *How NOT To Evaluate Your Dialogue System* | BLEU/ROUGE limitations in dialogue |
| Zheng et al. (NeurIPS 2023) — *Judging LLM-as-a-Judge* | Judge bias and debiasing |
| Liang et al. (Stanford CRFM 2022) — *HELM* | Reproducibility in evaluation |
| Wang et al. (ACL 2024) — *LLMs are not Fair Evaluators* | Judge calibration |
| Papineni et al. (ACL 2002) — *BLEU* | Reference-based metric design |

---

## Experiments

A separate branch, `experiments`, explores alternative judge configurations and evaluation workflows.

It includes a comparison page that runs the same test cases through both Gemini 2.5 Flash and DeepSeek-R1 (via Groq API) side by side, allowing differences in scoring behavior and reasoning style to be inspected interactively.

The branch was mainly used to explore:
- judge variability across models
- reasoning transparency
- alternative evaluation designs
- lightweight experimentation workflows

[View experiments branch](https://github.com/Vaishnavi-cyber-blip/KisanBot/tree/experiments)

# AI Use Disclosure

AI tools including Claude and ChatGPT were used throughout development.

They assisted with:

- GitHub issue drafting
- UI generation
- Python scaffolding
- debugging guidance
- literature explanation
- README refinement

Several claims were revised after deeper inspection of the repository and runtime behavior.

Examples:

- An initial assumption about unenforced `LLM_AS_JUDGE` routing was corrected after inspecting `importer/main.py`
- Benchmark concerns were refined after inspecting `DataPoints.json`
- Gemini model configuration changed after API compatibility testing
- The deprecated `google.generativeai` package was replaced with `google-genai`

What I did independently:

- CeRAI installation and setup attempts
- evaluation execution
- debugging Windows/WSL/Docker issues
- interpreting evaluation outputs
- designing the `task_type → metrics` routing approach
- deciding the overall evaluation framework structure

---

# Final Note

ConvEval is not intended to replace larger evaluation platforms.

It is a small prototype built around one central idea:

> conversational AI evaluation should depend on the type of conversational task being evaluated.

Open-ended advice, factual QA, multilingual interaction, and safety refusal should not all be evaluated using the same metric family.
