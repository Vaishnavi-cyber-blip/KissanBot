"""
core/evaluator.py
 
Task-aware evaluation pipeline.
 
Core design: task_type determines which metrics run.
This directly addresses CeRAI Issue #1 — BLEU/ROUGE applied indiscriminately.
 
Pipeline per test case:
  1. Send prompt to KisanBot → get response
  2. Look up allowed_metrics from task_type
  3. Run each metric through the appropriate judge prompt
  4. Return structured result with per-metric scores + reasoning
"""
 
import time
from dataclasses import dataclass, field
from typing import Optional
from core.kisanbot import get_response
from core.judge import LLMJudge
from core.testcases import TestCase, METRIC_DISPLAY_NAMES, METRIC_DESCRIPTIONS
 
 
@dataclass
class MetricResult:
    metric: str
    display_name: str
    description: str
    score: Optional[float]
    reasoning: str
    confidence: Optional[float]
    score_run_1: Optional[float]
    score_run_2: Optional[float]
    debiased: bool
 
    def score_label(self) -> str:
        if self.score is None:
            return "N/A"
        if self.score >= 0.8:
            return "✅ Pass"
        if self.score >= 0.5:
            return "⚠️ Partial"
        return "❌ Fail"
 
    def score_color(self) -> str:
        if self.score is None:
            return "gray"
        if self.score >= 0.8:
            return "green"
        if self.score >= 0.5:
            return "orange"
        return "red"
 
 
@dataclass
class CaseResult:
    case_id: str
    task_type: str
    category: str
    domain: str
    prompt: str
    bot_response: str
    reference_answer: Optional[str]
    metrics: list  # List[MetricResult]
    execution_status: str  # SUCCESS or FAILED
    error: Optional[str]
    latency_ms: int
    notes: str
 
    def mean_score(self) -> Optional[float]:
        scores = [m.score for m in self.metrics if m.score is not None]
        if not scores:
            return None
        return round(sum(scores) / len(scores), 3)
 
    def passed(self) -> bool:
        s = self.mean_score()
        return s is not None and s >= 0.7
 
 
def run_evaluation(
    test_cases: list,
    api_key: str,
    debias: bool = True,
    progress_callback=None,
) -> list:
    """
    Run full evaluation across all test cases.
 
    Args:
        test_cases: List of TestCase objects
        api_key: Gemini API key (used for both KisanBot and judge)
        debias: Whether to apply swap-order debiasing
        progress_callback: Optional function(i, total, case_id) for UI progress
 
    Returns:
        List of CaseResult objects
    """
    judge = LLMJudge(api_key=api_key, debias=debias)
    results = []
 
    for i, tc in enumerate(test_cases):
        if progress_callback:
            progress_callback(i, len(test_cases), tc.id)
 
        result = evaluate_single_case(tc, api_key, judge)
        results.append(result)
 
        # Small delay to avoid rate limiting
        time.sleep(4)
 
    if progress_callback:
        progress_callback(len(test_cases), len(test_cases), "done")
 
    return results
 
 
def evaluate_single_case(
    tc: TestCase,
    api_key: str,
    judge: LLMJudge,
) -> CaseResult:
    """Evaluate a single test case."""
 
    # Step 1: Get bot response
    start = time.time()
    try:
        bot_response = get_response(
            user_message=tc.prompt,
            api_key=api_key,
            system_prompt=tc.system_prompt,
        )
        latency_ms = int((time.time() - start) * 1000)
        execution_status = "SUCCESS"
        error = None
    except Exception as e:
        bot_response = ""
        latency_ms = int((time.time() - start) * 1000)
        execution_status = "FAILED"
        error = str(e)
 
    if execution_status == "FAILED":
        return CaseResult(
            case_id=tc.id,
            task_type=tc.task_type,
            category=tc.category,
            domain=tc.domain,
            prompt=tc.prompt,
            bot_response="",
            reference_answer=tc.reference_answer,
            metrics=[],
            execution_status="FAILED",
            error=error,
            latency_ms=latency_ms,
            notes=tc.notes,
        )
 
    # Step 2: Score each metric
    # task_type determines WHICH metrics run — this is the key design decision
    metric_results = []
    for metric in tc.get_metrics():
        judge_result = judge.score(
            metric=metric,
            prompt=tc.prompt,
            response=bot_response,
            reference=tc.reference_answer,
        )
 
        metric_results.append(MetricResult(
            metric=metric,
            display_name=METRIC_DISPLAY_NAMES.get(metric, metric),
            description=METRIC_DESCRIPTIONS.get(metric, ""),
            score=judge_result.get("score"),
            reasoning=judge_result.get("reasoning", ""),
            confidence=judge_result.get("confidence"),
            score_run_1=judge_result.get("score_run_1"),
            score_run_2=judge_result.get("score_run_2"),
            debiased=judge_result.get("debiased", False),
        ))
 
        # Small delay between metric calls
        time.sleep(3)
 
    return CaseResult(
        case_id=tc.id,
        task_type=tc.task_type,
        category=tc.category,
        domain=tc.domain,
        prompt=tc.prompt,
        bot_response=bot_response,
        reference_answer=tc.reference_answer,
        metrics=metric_results,
        execution_status="SUCCESS",
        error=None,
        latency_ms=latency_ms,
        notes=tc.notes,
    )
 
 
def build_summary(results: list) -> dict:
    """Build aggregate summary across all results."""
    total = len(results)
    successful = [r for r in results if r.execution_status == "SUCCESS"]
    passed = [r for r in successful if r.passed()]
 
    # Per task_type breakdown
    by_type = {}
    for r in successful:
        by_type.setdefault(r.task_type, []).append(r)
 
    type_summary = {}
    for task_type, cases in by_type.items():
        scores = [c.mean_score() for c in cases if c.mean_score() is not None]
        type_summary[task_type] = {
            "count": len(cases),
            "mean_score": round(sum(scores) / len(scores), 3) if scores else None,
            "passed": sum(1 for c in cases if c.passed()),
        }
 
    # Per metric breakdown
    metric_scores = {}
    for r in successful:
        for m in r.metrics:
            if m.score is not None:
                metric_scores.setdefault(m.metric, []).append(m.score)
 
    metric_summary = {}
    for metric, scores in metric_scores.items():
        metric_summary[metric] = {
            "mean": round(sum(scores) / len(scores), 3),
            "min": round(min(scores), 3),
            "max": round(max(scores), 3),
            "n": len(scores),
            "display_name": METRIC_DISPLAY_NAMES.get(metric, metric),
        }
 
    return {
        "total": total,
        "successful": len(successful),
        "failed": total - len(successful),
        "passed": len(passed),
        "pass_rate": round(len(passed) / len(successful), 3) if successful else 0,
        "overall_mean": round(
            sum(r.mean_score() for r in successful if r.mean_score()) /
            max(len(successful), 1), 3
        ),
        "by_task_type": type_summary,
        "by_metric": metric_summary,
    }