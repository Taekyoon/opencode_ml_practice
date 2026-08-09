"""연구용 데이터셋 등록/감시/로드 관리자.

사용자가 `research/inbox/`에 CSV를 넣으면:
1. `scan_inbox()` 가 미등록 파일을 감지한다
2. `register_file()` 이 datasets/<이름>/ 폴더로 복사하고, 대상 컬럼을 자동 추정하여
   research.db 의 datasets 테이블에 메타데이터를 기록한다
3. `load_dataset()` 로 실험 runner가 사용할 (X, y)를 준비한다

에이전트(ml-researcher)는 기본적으로 이 모듈을 통해 데이터를 다룬다.
"""

import json
import os
import shutil
import sqlite3
from datetime import datetime

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOX_DIR = os.path.join(PROJECT_ROOT, "research", "inbox")
DATASET_DIR = os.path.join(PROJECT_ROOT, "research", "datasets")
DB_PATH = os.path.join(PROJECT_ROOT, "research", "research.db")

TARGET_CANDIDATES = ["failure", "target", "label", "y", "defect", "thickness"]

DATASET_SCHEMA = """
CREATE TABLE IF NOT EXISTS datasets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    source_file TEXT NOT NULL,
    target_col TEXT,
    feature_cols TEXT NOT NULL,
    n_rows INTEGER NOT NULL,
    failure_rate REAL,
    registered_at TEXT NOT NULL,
    note TEXT,
    text_col TEXT
);
"""

_MIGRATION_TEXT_COL = "ALTER TABLE datasets ADD COLUMN text_col TEXT"


def _migrate_schema(conn):
    """기존 DB에 신규 컬럼(text_col)이 없는 경우 추가한다."""
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(datasets)").fetchall()}
    if "text_col" not in cols:
        conn.execute(_MIGRATION_TEXT_COL)
        conn.commit()


def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(DATASET_SCHEMA)
    _migrate_schema(conn)
    return conn


def scan_inbox() -> list[str]:
    """inbox 폴더의 미등록 CSV/parquet 파일 목록."""
    if not os.path.isdir(INBOX_DIR):
        return []
    return sorted(
        f
        for f in os.listdir(INBOX_DIR)
        if f.endswith(".csv") or f.endswith(".parquet")
    )


def _guess_target(df: pd.DataFrame) -> str | None:
    for col in TARGET_CANDIDATES:
        if col in df.columns:
            return col
    return None


def _safe_name(filename: str) -> str:
    base = os.path.splitext(os.path.basename(filename))[0]
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in base)


def _unique_name(name: str) -> str:
    conn = _conn()
    i = 1
    candidate = name
    while conn.execute("SELECT 1 FROM datasets WHERE name=?", (candidate,)).fetchone():
        i += 1
        candidate = f"{name}_{i}"
    conn.close()
    return candidate


def register_file(
    filename: str,
    target_col: str = None,
    note: str = None,
    name: str = None,
    text_col: str = None,
) -> dict:
    """inbox 의 데이터 파일을 등록한다.

    text_col 은 텍스트 분류 태스크용으로, 데이터의 "본문(프롬프트)" 컬럼을 지정한다.
    텍스트가 아닌 일반 수치 태스크에서는 쓰지 않아도 된다.
    """
    src = os.path.join(INBOX_DIR, filename)
    if not os.path.isfile(src):
        raise FileNotFoundError(f"{src} 없음")

    df = pd.read_csv(src) if filename.endswith(".csv") else pd.read_parquet(src)

    if target_col is None:
        target_col = _guess_target(df)
    if target_col is not None and target_col not in df.columns:
        raise ValueError(f"target '{target_col}' 이 데이터에 없습니다. 컬럼: {list(df.columns)}")
    if text_col is not None and text_col not in df.columns:
        raise ValueError(f"text_col '{text_col}' 이 데이터에 없습니다. 컬럼: {list(df.columns)}")
    if text_col is not None and text_col == target_col:
        raise ValueError("text_col 과 target_col 은 같을 수 없습니다.")

    ds_name = _unique_name(name or _safe_name(filename))
    dest_dir = os.path.join(DATASET_DIR, ds_name)
    os.makedirs(dest_dir, exist_ok=True)
    dest_file = os.path.join(dest_dir, os.path.basename(filename))
    shutil.copy2(src, dest_file)

    feature_cols = [c for c in df.columns if c != target_col] if target_col else list(df.columns)
    failure_rate = None
    if target_col and df[target_col].dropna().isin([0, 1]).all():
        failure_rate = float(df[target_col].mean())

    conn = _conn()
    conn.execute(
        """
        INSERT INTO datasets (name, source_file, target_col, feature_cols, n_rows, failure_rate, registered_at, note, text_col)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ds_name,
            dest_file,
            target_col,
            json.dumps(feature_cols),
            int(len(df)),
            failure_rate,
            datetime.now().isoformat(),
            note,
            text_col,
        ),
    )
    conn.commit()
    conn.close()

    os.remove(src)
    return {
        "name": ds_name,
        "target_col": target_col,
        "text_col": text_col,
        "feature_cols": feature_cols,
        "n_rows": int(len(df)),
        "failure_rate": failure_rate,
    }


def list_datasets() -> list[dict]:
    conn = _conn()
    rows = conn.execute("SELECT * FROM datasets ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_dataset(name: str) -> dict:
    conn = _conn()
    row = conn.execute("SELECT * FROM datasets WHERE name=?", (name,)).fetchone()
    conn.close()
    if row is None:
        raise KeyError(f"dataset '{name}' 없음")
    return dict(row)


def load_dataset(name: str) -> tuple[pd.DataFrame, pd.Series | None]:
    """dataset 을 (X, y)로 로드한다. target이 없으면 y=None.

    y 는 원본 dtype 을 보존한다 (숫자·문자열 모두). 도메인에 맞는 캐스팅은
    러너가 kind(=tasks_registry.infer_kind) 기준으로 수행한다.
    """
    meta = get_dataset(name)
    df = pd.read_csv(meta["source_file"])
    target = meta["target_col"]
    if target and target in df.columns:
        y = df[target]
        X = df.drop(columns=[target])
    else:
        y = None
        X = df
    return X, y


if __name__ == "__main__":
    print("inbox 파일:", scan_inbox())
    print("등록된 datasets:")
    for d in list_datasets():
        print(f"  {d['name']}: target={d['target_col']} rows={d['n_rows']}")