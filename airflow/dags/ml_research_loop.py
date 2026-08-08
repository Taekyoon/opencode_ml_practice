"""매일 밤 자율 ML 연구 루프 DAG.

1. prepare_data   — (준비 완료 단계, 실험 데이터 예산 확인용)
2. run_experiment — experiment_runner.py 실행 (에이전트가 수정한 단일 파일)
3. evaluate_store — 결과 평가 + SQLite 기록 + best_model 갱신
4. report         — 일일 리포트 생성

에이전트(ml-researcher)는 연구 지침서(research_program.md)에 따라
experiment_runner.py 를 수정한 뒤 이 DAG를 트리거한다.
"""

import json
import os
import subprocess
import sys
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

# 프로젝트 루트
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

RUN_DIR = os.path.join(PROJECT_ROOT, "research", "results")
REPORT_DIR = os.path.join(PROJECT_ROOT, "research", "reports")

DEFAULT_ARGS = {
    "owner": "ml-researcher",
    "retries": 1,
    "depends_on_past": False,
    "email_on_failure": False,
}


def _prepare_data(**context):
    """사용할 실험 데이터 소스 확인. (이미 src/ 로 고정됨)"""
    from src.data_generation import generate_synthetic_data

    df = generate_synthetic_data(n_samples=5000, seed=42)
    context["task_instance"].xcom_push(
        key="data_summary",
        value={"rows": len(df), "failure_rate": float(df["failure"].mean())},
    )
    return {"data_ready": True, "rows": len(df)}


def _run_experiment(**context):
    """experiment_runner.py 를 subprocess로 실행하여 결과 JSON을 반환."""
    runner = os.path.join(PROJECT_ROOT, "experiment_runner.py")
    python = sys.executable

    import tempfile
    out_tmp = tempfile.mktemp(suffix=".json", prefix="exp_", dir="/tmp")

    # runner가 stdout으로 JSON 출력하도록, 하위 프로세스에서 임시 run_dir 사용
    proc = subprocess.run(
        [python, runner],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        timeout=300,  # 5분 예산
    )
    if proc.returncode != 0:
        raise RuntimeError(f"experiment_runner.py 실패:\n{proc.stdout}\n{proc.stderr}")

    # metrics.json 을 최신 run_*/ 폴더에서 찾는다
    run_dirs = sorted(
        (d for d in os.listdir(RUN_DIR) if d.startswith("run_") and os.path.isdir(os.path.join(RUN_DIR, d))),
        reverse=True,
    )
    if not run_dirs:
        raise FileNotFoundError("실험 결과 폴더가 없습니다.")

    latest = os.path.join(RUN_DIR, run_dirs[0], "metrics.json")
    with open(latest, encoding="utf-8") as f:
        result = json.load(f)

    result["run_id"] = os.path.basename(run_dirs[0])
    context["task_instance"].xcom_push(key="run_result", value=result)

    # runner 스냅샷 저장 (재현성)
    snap_src = ""
    snap_path = os.path.join(RUN_DIR, run_dirs[0], "runner_snapshot.py")
    if os.path.exists(snap_path):
        with open(snap_path, encoding="utf-8") as f:
            snap_src = f.read()

    context["task_instance"].xcom_push(key="runner_snapshot", value=snap_src)
    return result


def _evaluate_store(**context):
    """결과를 SQLite에 기록하고 best_model 을 갱신한다."""
    ti = context["task_instance"]
    result = ti.xcom_pull(task_ids="run_experiment", key="run_result")
    snap_src = ti.xcom_pull(task_ids="run_experiment", key="runner_snapshot")

    from src.research_store import get_best_score, record_experiment

    run_id = result.get("run_id")
    score = result["score"]
    metrics = result["metrics"]
    config = result["config"]

    prev_best = get_best_score()
    record_experiment(
        run_id=run_id,
        config=config,
        metrics=metrics,
        score=score,
        runner_snapshot=snap_src,
    )
    new_best = get_best_score()

    return {
        "run_id": run_id,
        "score": score,
        "prev_best": prev_best,
        "new_best": new_best,
        "improved": new_best is not None and (prev_best is None or new_best > prev_best),
    }


def _generate_report(**context):
    """일일 연구 리포트를 생성한다 (markdown)."""
    from src.research_store import get_all_experiments

    ti = context["task_instance"]
    eval_info = ti.xcom_pull(task_ids="evaluate_store")

    os.makedirs(REPORT_DIR, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    report_path = os.path.join(REPORT_DIR, f"report_{date_str}.md")

    records = get_all_experiments(limit=20)
    lines = [
        f"# ML 자율 연구 리포트 ({date_str})",
        "",
        "## 오늘의 실험",
        f"- 실행한 실험: {eval_info['run_id']}",
        f"- score: {eval_info['score']} (이전 최고: {eval_info['prev_best']}, 현재 최고: {eval_info['new_best']})",
        f"- 개선 여부: {'개선됨' if eval_info.get('improved') else '미개선'}",
        "",
        "## 최근 실험 기록",
        "",
    ]
    for r in records:
        lines.append(
            f"- `{r['run_id']}` score={r['score']} F1={r.get('f1')} PR-AUC={r.get('pr_auc')} is_best={'★' if r.get('is_best') else ''}"
        )
    lines.append("")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[report] 생성됨: {report_path}")
    return {"report_path": report_path}


with DAG(
    dag_id="ml_research_loop",
    default_args=DEFAULT_ARGS,
    schedule_interval="0 0 * * *",  # 매일 밤(UTC 기준) 0시
    start_date=datetime(2026, 8, 1),
    catchup=False,
    tags=["semiconductor", "research", "ml-researcher"],
    description="자율 ML 연구 루프: experiment_runner.py 실행 → 평가 → 기록 → 리포트",
) as dag:

    t_prepare = PythonOperator(
        task_id="prepare_data",
        python_callable=_prepare_data,
    )
    t_run = PythonOperator(
        task_id="run_experiment",
        python_callable=_run_experiment,
    )
    t_eval = PythonOperator(
        task_id="evaluate_store",
        python_callable=_evaluate_store,
    )
    t_report = PythonOperator(
        task_id="generate_report",
        python_callable=_generate_report,
    )

    t_prepare >> t_run >> t_eval >> t_report