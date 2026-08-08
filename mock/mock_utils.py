"""모의 실험 데이터베이스 및 알림 유틸리티 (데모용).

실제 DB/Slack이 없는 환경에서 Airflow 파이프라인을 검증하기 위한 목업이다.
- 데이터베이스: SQLite (mock/experiment_data.db)
- 알림: 파일 기반 (mock/notifications/*.json)
"""

import json
import os
import sqlite3
from datetime import datetime

import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOCK_DIR = os.path.join(BASE_DIR, "mock")
DB_PATH = os.path.join(MOCK_DIR, "experiment_data.db")
NOTIFICATION_DIR = os.path.join(MOCK_DIR, "notifications")

FEATURE_COLS = [
    "temperature",
    "pressure",
    "process_time",
    "chemical_concentration",
    "thickness",
    "resistivity",
    "dopant",
]

RANDOM_SEED = 42


def create_mock_database(db_path: str = DB_PATH) -> sqlite3.Connection:
    """SQLite 모의 데이터베이스를 생성하고 접속한다."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS experiment_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            temperature REAL,
            pressure REAL,
            process_time REAL,
            chemical_concentration REAL,
            thickness REAL,
            resistivity REAL,
            dopant REAL,
            failure INTEGER
        )
        """
    )
    conn.commit()
    return conn


def insert_daily_data(
    date: str, n_samples: int = 1500, seed: int = RANDOM_SEED, db_path: str = DB_PATH
) -> int:
    """특정 날짜의 실험 데이터를 생성해 모의 DB에 삽입한다. (date 기반 시드)

    failure 라벨은 공정 변수(온도/압력/화학농도/공정시간)의 로짓 선형 결합으로
    생성되어 모델이 실제 패턴을 학습할 수 있도록 한다. 불량률 약 16.7%.
    """
    rng = np.random.default_rng(seed + sum(bytearray(date.encode())))

    temperature = rng.uniform(20.0, 300.0, n_samples)
    pressure = rng.uniform(1.0, 10.0, n_samples)
    process_time = rng.uniform(1.0, 60.0, n_samples)
    chemical_concentration = rng.uniform(0.1, 10.0, n_samples)
    thickness = 500 + 2.0 * temperature - 30.0 * pressure + rng.normal(0, 25, n_samples)
    resistivity = 50 - 0.15 * temperature + rng.normal(0, 5, n_samples)
    dopant = 2.0 - 0.3 * chemical_concentration + rng.normal(0, 0.5, n_samples)

    data = {
        "date": date,
        "temperature": temperature,
        "pressure": pressure,
        "process_time": process_time,
        "chemical_concentration": chemical_concentration,
        "thickness": thickness,
        "resistivity": resistivity,
        "dopant": dopant,
    }

    df = pd.DataFrame(data)

    logit = (
        -10.5
        + 0.8 * (temperature - 150.0) / 80.0
        - 1.2 * (pressure - 5.5) / 2.5
        + 1.0 * (chemical_concentration - 5.0) / 3.0
        - 0.6 * (process_time - 30.0) / 17.0
        + 0.7 * (thickness - thickness.mean()) / 25.0
        - 0.5 * (resistivity - 50.0) / 5.0
    )
    prob_failure = 1.0 / (1.0 + np.exp(-logit))
    df["failure"] = rng.binomial(1, prob_failure).astype(int)

    conn = create_mock_database(db_path)
    df.to_sql("experiment_data", conn, if_exists="append", index=False)
    conn.close()
    return len(df)


def load_data_by_date(date: str, db_path: str = DB_PATH) -> pd.DataFrame:
    """특정 날짜의 실측 데이터를 DB에서 로드한다."""
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(
        f"SELECT * FROM experiment_data WHERE date = '{date}' ORDER BY id", conn
    )
    conn.close()
    return df


def send_notification(message: str, level: str = "info") -> str:
    """파일 기반 알림. mock/notifications/ 아래 JSON 파일로 기록한다."""
    os.makedirs(NOTIFICATION_DIR, exist_ok=True)
    notification = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "message": message,
    }
    filename = os.path.join(
        NOTIFICATION_DIR, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{level}.json"
    )
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(notification, f, indent=2, ensure_ascii=False)
    print(f"[알림] ({level}) {message}")
    return filename