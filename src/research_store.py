"""자율 ML 연구 실험 기록 관리 모듈.

- SQLite: research/research.db
  - experiments 테이블: 실험 실행 기록 (config, score, keep/discard 판정)
  - best_run 테이블: 최고 성능 기록
"""

import json
import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESEARCH_DIR = os.path.join(BASE_DIR, "research")
DB_PATH = os.path.join(RESEARCH_DIR, "research.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS experiments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date TEXT NOT NULL,
    run_id TEXT UNIQUE NOT NULL,
    config_json TEXT NOT NULL,
    score REAL NOT NULL,
    f1 REAL,
    pr_auc REAL,
    roc_auc REAL,
    precision REAL,
    recall REAL,
    accuracy REAL,
    elapsed_sec REAL,
    status TEXT DEFAULT 'completed',
    is_best INTEGER DEFAULT 0,
    runner_snapshot TEXT
);

CREATE TABLE IF NOT EXISTS best_run (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT UNIQUE NOT NULL,
    score REAL NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def get_conn(db_path: str = DB_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def record_experiment(
    run_id: str,
    config: dict,
    metrics: dict,
    score: float,
    runner_snapshot: str = None,
    db_path: str = DB_PATH,
) -> int:
    """실험 실행 결과를 experiments 테이블에 기록한다. best 여부도 판정."""
    conn = get_conn(db_path)
    status = "completed"
    if metrics is None:
        status = "failed"

    cur = conn.execute(
        """
        INSERT INTO experiments
        (run_date, run_id, config_json, score, f1, pr_auc, roc_auc,
         precision, recall, accuracy, elapsed_sec, status, runner_snapshot)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now().strftime("%Y-%m-%d"),
            run_id,
            json.dumps(config, ensure_ascii=False),
            score if metrics else 0.0,
            metrics.get("f1") if metrics else None,
            metrics.get("pr_auc") if metrics else None,
            metrics.get("roc_auc") if metrics else None,
            metrics.get("precision") if metrics else None,
            metrics.get("recall") if metrics else None,
            metrics.get("accuracy") if metrics else None,
            metrics.get("elapsed_sec") if metrics else None,
            status,
            runner_snapshot,
        ),
    )
    exp_id = cur.lastrowid
    conn.commit()

    # 최고 기록 갱신 (is_best 마킹)
    if status == "completed":
        best = conn.execute("SELECT MAX(score) AS best FROM experiments WHERE status='completed'").fetchone()
        if best["best"] is None or score >= best["best"]:
            conn.execute("UPDATE experiments SET is_best=0 WHERE is_best=1")
            conn.execute("UPDATE experiments SET is_best=1 WHERE id=?", (exp_id,))
            conn.execute("DELETE FROM best_run")
            conn.execute(
                "INSERT INTO best_run (run_id, score, updated_at) VALUES (?, ?, ?)",
                (run_id, score, datetime.now().isoformat()),
            )
            conn.commit()
            print(f"[research] 최고 기록 갱신: run_id={run_id}, score={score}")

    conn.close()
    return exp_id


def get_best_score(db_path: str = DB_PATH) -> float | None:
    conn = get_conn(db_path)
    row = conn.execute("SELECT MAX(score) AS best FROM experiments WHERE status='completed'").fetchone()
    conn.close()
    return row["best"] if row and row["best"] is not None else None


def get_all_experiments(limit: int = 50, db_path: str = DB_PATH) -> list[dict]:
    conn = get_conn(db_path)
    rows = conn.execute(
        "SELECT * FROM experiments ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    conn = get_conn()
    print("이전 실험 기록:")
    for row in get_all_experiments(limit=10):
        print(f"  id={row['id']} run={row['run_id']} score={row['score']} is_best={row['is_best']}")