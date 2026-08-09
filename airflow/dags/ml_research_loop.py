"""매일 밤 자율 ML 연구 루프 DAG (다중 태스크).

research/tasks_registry.py 의 등록된 task를 모두 읽어 task별로 실험을 수행한다.

- conf 미지정: 등록된 모든 task 실행 (매일 스케줄)
- conf 지정:      airflow dags trigger ml_research_loop -c '{"task": "quality_regression"}' \
                  해당 task만 실행, 나머지는 skip

task 흐름: prepare_data → run_experiment → evaluate_store → generate_report
"""

import json
import os
import re
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
    """task별 experiment_runner.py 를 subprocess 로 실행한다.

    실행 시작/완료/실패를 events 테이블에 기록한다 (실패도 기록 — 실패한 실험이
    DB에 존재하지 않는 상태를 방지, J1 실행 이벤트 기록의 핵심).
    """
    _guard(task_id, context)
    task = get_task(task_id)
    runner = os.path.join(PROJECT_ROOT, task.runner)
    results_dir = os.path.join(PROJECT_ROOT, task.results_dir)

    from src.research_store import record_event

    # 실패 시 사용할 임시 run_id (experiments 행과는 독립)
    fail_run_id = f"{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    record_event(fail_run_id, "started", {"task_id": task_id, "runner": task.runner})

    proc = subprocess.run(
        [sys.executable, runner],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        timeout=300,
    )
    if proc.returncode != 0:
        record_event(
            fail_run_id,
            "failed",
            {
                "task_id": task_id,
                "returncode": proc.returncode,
                "stderr_tail": proc.stderr[-500:],
            },
        )
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
        error = f"{task_id}: 실험 결과 폴더가 없습니다."
        record_event(fail_run_id, "failed", {"task_id": task_id, "error": error})
        raise FileNotFoundError(error)

    latest = os.path.join(results_dir, run_dirs[0], "metrics.json")
    with open(latest, encoding="utf-8") as f:
        result = json.load(f)
    result["run_id"] = os.path.basename(run_dirs[0])

    snap_src = ""
    snap_path = os.path.join(results_dir, run_dirs[0], "runner_snapshot.py")
    if os.path.exists(snap_path):
        with open(snap_path, encoding="utf-8") as f:
            snap_src = f.read()

    record_event(
        result["run_id"],
        "completed",
        {"task_id": task_id, "score": result.get("score")},
    )

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
        "metrics": result["metrics"],
        "prev_best": prev_best,
        "new_best": new_best,
        "improved": new_best is not None and prev_best is not None and new_best > prev_best,
    }


def _update_wiki(task_id: str, eval_info: dict):
    """실험 결과를 research/wiki/ 에 반영한다 (Ingest 자동화).

    1. tasks/<task_id>.md 의 "현재 최고 결과" 표에 새 run 행 추가 (★ = 신규 최고)
    2. log.md 에 append (연대기 기록)
    """
    WIKI_DIR = os.path.join(PROJECT_ROOT, "research", "wiki")
    task_page = os.path.join(WIKI_DIR, "tasks", f"{task_id}.md")
    log_path = os.path.join(WIKI_DIR, "log.md")
    os.makedirs(os.path.dirname(task_page), exist_ok=True)
    if not os.path.exists(log_path):
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as _f:
            _f.write("# Research Wiki — Activity Log\n\n")
        print(f"[wiki] log.md 없어 생성")

    run_id = eval_info["run_id"]
    score = eval_info["score"]
    metrics = eval_info.get("metrics") or {}
    improved = bool(eval_info.get("improved"))
    date_str = datetime.now().strftime("%Y-%m-%d")
    # metrics.json 의 지표 채움 (회귀/분류 표 열 구조에 맞게)
    f1 = metrics.get("f1")
    pr_auc = metrics.get("pr_auc")
    rmse = metrics.get("rmse")

    # 1) task 페이지 "현재 최고 결과" 표의 분리 행 바로 뒤에 새 행 삽입
    if os.path.exists(task_page):
        with open(task_page, encoding="utf-8") as f:
            content = f.read()
        star = "★ " if improved else ""
        # 분류 표: run_id | score(F1×PR-AUC) | F1 | PR-AUC | 핵심 변경사항
        # 회귀 표: run_id | score(R²) | RMSE | 핵심 변경사항
        if task_id == "quality_regression" or (metrics and rmse is not None):
            new_row = f"| {run_id} | **{score}** | {rmse if rmse is not None else '—'} | {date_str} {star}(자동 기록) |"
        else:
            new_row = f"| {run_id} | **{score}** | {f1 if f1 is not None else '—'} | {pr_auc if pr_auc is not None else '—'} | {date_str} {star}(자동 기록) |"
        # "현재 최고 결과" 섹션 안 첫 번째 표의 분리 행(|---|...) 다음에 삽입
        inserted = re.sub(
            r"(## 현재 최고 결과.*?\n\|[-| :]+ *\| *\n)",
            lambda m: m.group(1) + new_row + "\n",
            content,
            count=1,
            flags=re.DOTALL,
        )
        if inserted != content:
            with open(task_page, "w", encoding="utf-8") as f:
                f.write(inserted)
            print(f"[wiki:{task_id}] 최고 결과 표에 run 기록 (run={run_id}, score={score})")
        else:
            print(f"[wiki:{task_id}] 최고 결과 표 패턴 미일치 → 수동 갱신 권장: {task_id}")
    else:
        print(f"[wiki:{task_id}] tasks 페이지 없음 → 수동 생성 필요: {task_page}")

    # 2) log.md append (파일 끝 개행 보장 — grep "^## \[" 파싱 계약 유지)
    with open(log_path, "rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        ends_with_nl = False
        if size > 0:
            f.seek(size - 1)
            ends_with_nl = f.read(1) == b"\n"
    with open(log_path, "a", encoding="utf-8") as f:
        if size > 0 and not ends_with_nl:
            f.write("\n")
        entry = f"## [{date_str}] ingest | {task_id} | {run_id} | score={score}"
        if improved:
            entry += " | BEST"
        f.write(entry + "\n")
    print(f"[wiki:{task_id}] log.md 기록")

    return {"wiki_updated": True}


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

    # wiki 반영 (Ingest 자동화)
    _update_wiki(task_id, eval_info)

    return {"report_path": report_path, "wiki_updated": True}


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