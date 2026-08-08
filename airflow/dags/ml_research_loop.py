"""매일 밤 자율 ML 연구 루프 DAG (다중 태스크).

research/tasks_registry.py 의 등록된 task를 모두 읽어 task별로 실험을 수행한다.

- conf 미지정: 등록된 모든 task 실행 (매일 스케줄)
- conf 지정:      airflow dags trigger ml_research_loop -c '{"task": "quality_regression"}' \
                  해당 task만 실행, 나머지는 skip

task 흐름: prepare_data → run_experiment → evaluate_store → generate_report
"""

import json
import os
import subprocess
import sys
from datetime import datetime

from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.python import PythonOperator

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "research"))

from tasks_registry import get_task, list_tasks

REPORT_DIR = os.path.join(PROJECT_ROOT, "research", "reports")

DEFAULT_ARGS = {
    "owner": "ml-researcher",
    "retries": 1,
    "depends_on_past": False,
    "email_on_failure": False,
}


def _selected_tasks(conf: dict) -> list:
    """conf['task'] 또는 conf['tasks']로 선택된 task 리스트. 미지정 시 전체."""
    if not conf:
        return list_tasks()
    raw = conf.get("tasks") or conf.get("task")
    if not raw:
        return list_tasks()
    if isinstance(raw, str):
        raw = [raw]
    return [get_task(t).id for t in raw]


def _guard(task_id: str, context: dict):
    """conf 로 선택된 task 가 아니면 이 task 를 skip 한다."""
    conf = (context.get("dag_run") or {}).conf if context.get("dag_run") else None
    requested = _selected_tasks(conf)
    if requested and task_id not in requested:
        raise AirflowSkipException(f"{task_id}: 이번 실행 대상이 아님 (conf={conf})")


def _prepare_data(task_id: str, **context):
    """데이터 준비 확인 (데이터 생성은 src/ 고정, 무상태 체크)."""
    _guard(task_id, context)
    return {"task_id": task_id, "data_ready": True}


def _run_experiment(task_id: str, **context):
    """task별 experiment_runner.py 를 subprocess 로 실행한다."""
    _guard(task_id, context)
    task = get_task(task_id)
    runner = os.path.join(PROJECT_ROOT, task.runner)
    results_dir = os.path.join(PROJECT_ROOT, task.results_dir)

    proc = subprocess.run(
        [sys.executable, runner],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        timeout=300,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"{task_id} runner 실패:\n{proc.stdout}\n{proc.stderr}")

    run_dirs = sorted(
        (
            d
            for d in os.listdir(results_dir)
            if d.startswith("run_") and os.path.isdir(os.path.join(results_dir, d))
        ),
        reverse=True,
    )
    if not run_dirs:
        raise FileNotFoundError(f"{task_id}: 실험 결과 폴더가 없습니다.")

    latest = os.path.join(results_dir, run_dirs[0], "metrics.json")
    with open(latest, encoding="utf-8") as f:
        result = json.load(f)
    result["run_id"] = os.path.basename(run_dirs[0])

    snap_src = ""
    snap_path = os.path.join(results_dir, run_dirs[0], "runner_snapshot.py")
    if os.path.exists(snap_path):
        with open(snap_path, encoding="utf-8") as f:
            snap_src = f.read()

    context["task_instance"].xcom_push(key="run_result", value=result)
    context["task_instance"].xcom_push(key="runner_snapshot", value=snap_src)
    return result


def _evaluate_store(task_id: str, **context):
    """결과를 SQLite 에 기록하고 task 별 best 갱신."""
    _guard(task_id, context)
    ti = context["task_instance"]
    result = ti.xcom_pull(task_ids=f"{task_id}_run", key="run_result")
    snap_src = ti.xcom_pull(task_ids=f"{task_id}_run", key="runner_snapshot")
    task = get_task(task_id)

    from src.research_store import get_best_score, record_experiment

    prev_best = get_best_score(task_id)
    record_experiment(
        run_id=result["run_id"],
        config=result["config"],
        metrics=result["metrics"],
        score=result["score"],
        task_id=task_id,
        score_name=task.score_name,
        runner_snapshot=snap_src,
    )
    new_best = get_best_score(task_id)

    return {
        "task_id": task_id,
        "run_id": result["run_id"],
        "score": result["score"],
        "prev_best": prev_best,
        "new_best": new_best,
        "improved": new_best is not None and prev_best is not None and new_best > prev_best,
    }


def _generate_report(task_id: str, **context):
    """task별 일일 리포트 생성."""
    _guard(task_id, context)
    from src.research_store import get_all_experiments

    ti = context["task_instance"]
    eval_info = ti.xcom_pull(task_ids=f"{task_id}_eval")
    task = get_task(task_id)

    os.makedirs(REPORT_DIR, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    report_path = os.path.join(REPORT_DIR, f"report_{task_id}_{date_str}.md")

    records = get_all_experiments(task_id=task_id, limit=20)
    lines = [
        f"# ML 자율 연구 리포트 — {task_id} ({date_str})",
        "",
        f"## 태스크: {task.description}",
        "",
        "## 오늘의 실험",
        f"- 실행: `{eval_info['run_id']}`",
        f"- score: {eval_info['score']} (이전 최고: {eval_info['prev_best']}, 현재: {eval_info['new_best']})",
        f"- 개선 여부: {'개선됨' if eval_info.get('improved') else '미개선'}",
        "",
        "## 최근 실험 기록",
        "",
    ]
    for r in records:
        lines.append(
            f"- `{r['run_id']}` score={r['score']} "
            f"(F1={r.get('f1')}, PR-AUC={r.get('pr_auc')}, R2={r.get('r2')}) "
            f"{'★' if r.get('is_best') else ''}"
        )
    lines.append("")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[report:{task_id}] 생성됨: {report_path}")
    return {"report_path": report_path}


with DAG(
    dag_id="ml_research_loop",
    default_args=DEFAULT_ARGS,
    schedule_interval="0 0 * * *",  # 매일 밤 00:00 (UTC)
    start_date=datetime(2026, 8, 1),
    catchup=False,
    tags=["semiconductor", "research", "ml-researcher"],
    description="자율 ML 연구 루프 (다중 태스크): runner 실행 → 평가 → 기록 → 리포트",
) as dag:

    for task_id in list_tasks():
        t_prepare = PythonOperator(
            task_id=f"{task_id}_prepare",
            python_callable=_prepare_data,
            op_kwargs={"task_id": task_id},
            provide_context=True,
        )
        t_run = PythonOperator(
            task_id=f"{task_id}_run",
            python_callable=_run_experiment,
            op_kwargs={"task_id": task_id},
        )
        t_eval = PythonOperator(
            task_id=f"{task_id}_eval",
            python_callable=_evaluate_store,
            op_kwargs={"task_id": task_id},
        )
        t_report = PythonOperator(
            task_id=f"{task_id}_report",
            python_callable=_generate_report,
            op_kwargs={"task_id": task_id},
        )
        t_prepare >> t_run >> t_eval >> t_report