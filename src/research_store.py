"""자율 ML 연구 실험 기록 관리 모듈.

- SQLite: research/research.db
  - experiments 테이블: 실험 실행 기록 (task_id, config, score, keep/discard 판정)
  - best_run 테이블: task별 최고 성능 기록 (task_id 단위)

task_id 는 research/tasks_registry.py의 TASKS 키와 일치한다.
"""

import json
import os
import sqlite3
from datetime import datetime

from research.tasks_registry import DEFAULT_TASK

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESEARCH_DIR = os.path.join(BASE_DIR, "research")
DB_PATH = os.path.join(RESEARCH_DIR, "research.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS experiments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL DEFAULT 'failure_prediction',
    run_date TEXT NOT NULL,
    run_id TEXT UNIQUE NOT NULL,
    config_json TEXT NOT NULL,
    metrics_json TEXT,
    score REAL NOT NULL,
    score_name TEXT,
    f1 REAL,
    pr_auc REAL,
    roc_auc REAL,
    precision REAL,
    recall REAL,
    accuracy REAL,
    r2 REAL,
    elapsed_sec REAL,
    status TEXT DEFAULT 'completed',
    is_best INTEGER DEFAULT 0,
    runner_snapshot TEXT
);

CREATE TABLE IF NOT EXISTS best_run (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL UNIQUE,
    run_id TEXT NOT NULL,
    score REAL NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def get_conn(db_path: str = DB_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    _migrate_schema(conn)
    return conn


def _migrate_schema(conn):
    """기존 DB를 현재 SCHEMA와 일치하도록 마이그레이션한다."""
    exp_cols = {r["name"] for r in conn.execute("PRAGMA table_info(experiments)").fetchall()}
    additions = {
        "task_id": "TEXT NOT NULL DEFAULT 'failure_prediction'",
        "metrics_json": "TEXT",
        "score_name": "TEXT",
        "r2": "REAL",
    }
    for name, decl in additions.items():
        if name not in exp_cols:
            conn.execute(f"ALTER TABLE experiments ADD COLUMN {name} {decl}")

    best_cols = {r["name"] for r in conn.execute("PRAGMA table_info(best_run)").fetchall()}
    if "task_id" not in best_cols:
        # best_run은 파생 테이블이므로 재생성 (데이터는 experiments에서 복구 가능)
        conn.execute("DROP TABLE best_run")
        conn.execute(
            """CREATE TABLE IF NOT EXISTS best_run (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL UNIQUE,
                run_id TEXT NOT NULL,
                score REAL NOT NULL,
                updated_at TEXT NOT NULL
            )"""
        )
    conn.commit()


def _has_column(conn, table: str, column: str) -> bool:
    return any(
        r["name"] == column
        for r in conn.execute(f"PRAGMA table_info({table})").fetchall()
    )


def _row_score(metrics: dict) -> tuple:
    """실험 metrics에서 표준 점수 컬럼값들을 추출한다."""
    return (
        metrics.get("f1") if metrics else None,
        metrics.get("pr_auc") if metrics else None,
        metrics.get("roc_auc") if metrics else None,
        metrics.get("precision") if metrics else None,
        metrics.get("recall") if metrics else None,
        metrics.get("accuracy") if metrics else None,
        metrics.get("r2") if metrics else None,
    )


def record_experiment(
    run_id: str,
    config: dict,
    metrics: dict,
    score: float,
    runner_snapshot: str = None,
    task_id: str = DEFAULT_TASK,
    score_name: str = None,
    db_path: str = DB_PATH,
) -> int:
    """실험 실행 결과를 저장한다. task별 is_best 판정."""
    conn = get_conn(db_path)
    status = "completed"
    if metrics is None:
        status = "failed"

    f1, pr_auc, roc_auc, precision, recall, accuracy, r2 = _row_score(metrics)

    cur = conn.execute(
        """
        INSERT INTO experiments
        (task_id, run_date, run_id, config_json, metrics_json, score, score_name,
         f1, pr_auc, roc_auc, precision, recall, accuracy, r2,
         elapsed_sec, status, runner_snapshot)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            task_id,
            datetime.now().strftime("%Y-%m-%d"),
            run_id,
            json.dumps(config, ensure_ascii=False),
            json.dumps(metrics or {}, ensure_ascii=False),
            score if metrics else 0.0,
            score_name,
            f1,
            pr_auc,
            roc_auc,
            precision,
            recall,
            accuracy,
            r2,
            metrics.get("elapsed_sec") if metrics else None,
            status,
            runner_snapshot,
        ),
    )
    exp_id = cur.lastrowid
    conn.commit()

    # task별 최고 기록 갱신
    if status == "completed":
        best = conn.execute(
            "SELECT MAX(score) AS m FROM experiments WHERE status='completed' AND task_id=?",
            (task_id,),
        ).fetchone()
        if best["m"] is None or score >= best["m"]:
            conn.execute("UPDATE experiments SET is_best=0 WHERE is_best=1 AND task_id=?", (task_id,))
            conn.execute("UPDATE experiments SET is_best=1 WHERE id=?", (exp_id,))
            conn.execute(
                """
                INSERT INTO best_run (task_id, run_id, score, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    run_id=excluded.run_id, score=excluded.score, updated_at=excluded.updated_at
                """,
                (task_id, run_id, score, datetime.now().isoformat()),
            )
            conn.commit()
            print(f"[research] {task_id} 최고 기록 갱신: run_id={run_id}, score={score}")

    conn.close()
    return exp_id


def get_best_score(task_id: str = DEFAULT_TASK, db_path: str = DB_PATH) -> float | None:
    conn = get_conn(db_path)
    row = conn.execute(
        "SELECT MAX(score) AS best FROM experiments WHERE status='completed' AND task_id=?",
        (task_id,),
    ).fetchone()
    conn.close()
    return row["best"] if row else None


def get_all_experiments(task_id: str = None, limit: int = 50, db_path: str = DB_PATH) -> list[dict]:
    conn = get_conn(db_path)
    if task_id:
        rows = conn.execute(
            "SELECT * FROM experiments WHERE task_id=? ORDER BY id DESC LIMIT ?",
            (task_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM experiments ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_tasks_summary(db_path: str = DB_PATH) -> list[dict]:
    """task별 실험 수 / 최고 점수 요약."""
    conn = get_conn(db_path)
    rows = conn.execute(
        """
        SELECT task_id, COUNT(*) AS n, MAX(score) AS best_score
        FROM experiments WHERE status='completed'
        GROUP BY task_id ORDER BY task_id
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    print("등록된 태스크별 요약:")
    for row in list_tasks_summary():
        print(f"  {row['task_id']}: {row['n']}회 실험, 최고 score={row['best_score']}")
    if not list_tasks_summary():
        print("  (아직 실험 기록이 없음)")