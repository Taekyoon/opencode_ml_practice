"""반도체 제조 failure 예측을 위한 가상 수치 데이터 생성."""

import numpy as np
import pandas as pd

RANDOM_SEED = 42


def generate_synthetic_data(n_samples: int = 5000, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """반도체 공정/측정 변수와 failure 라벨을 갖는 가상 데이터를 생성한다.

    공정 변수: temperature, pressure, process_time, chemical_concentration
    측정 변수: thickness, resistance, dopant_density
    라벨: boolean (1=불량, 0=합격), 불량률 약 10%
    """
    rng = np.random.default_rng(seed)

    # --- 공정 변수 (동일 단위 없음 -> 스케일링 필요) ---
    temperature = rng.uniform(20.0, 300.0, n_samples)          # °C
    pressure = rng.uniform(1.0, 10.0, n_samples)               # atm
    process_time = rng.uniform(1.0, 60.0, n_samples)           # min
    chemical_concentration = rng.uniform(0.1, 10.0, n_samples) # M

    # --- 측정 변수 (공정 변수에 의존적으로 생성) ---
    thickness = 500 + 2.0 * temperature - 30.0 * pressure + rng.normal(0, 25, n_samples)
    resistivity = 50 - 0.15 * temperature + rng.normal(0, 5, n_samples)
    dopant = 2.0 - 0.3 * chemical_concentration + rng.normal(0, 0.5, n_samples)

    data = pd.DataFrame({
        "temperature": temperature,
        "pressure": pressure,
        "process_time": process_time,
        "chemical_concentration": chemical_concentration,
        "thickness": thickness,
        "resistivity": resistivity,
        "dopant": dopant,
    })

    # --- failure 라벨 생성 (로짓 확률 기반, 불량률 약 10%) ---
    logit = (
        -10.5
        + 0.8 * (temperature - 150.0) / 80.0
        - 1.2 * (pressure - 5.5) / 2.5
        + 1.0 * (chemical_concentration - 5.0) / 3.0
        - 0.6 * (process_time - 30.0) / 17.0
        + 0.7 * (thickness - data["thickness"].mean()) / 25.0
        - 0.5 * (resistivity - 50.0) / 5.0
    )
    prob_failure = 1.0 / (1.0 + np.exp(-logit))
    data["failure"] = (rng.random(n_samples) < prob_failure).astype(int)

    # 전체 불량률 확인 및 조정 (목표 10% 근처)
    current_rate = data["failure"].mean()
    print(f"생성 완료: {len(data)}행, 불량률 {current_rate:.1%}")

    return data


if __name__ == "__main__":
    df = generate_synthetic_data()
    df.to_csv("data/synthetic_data.csv", index=False)
    print(df.head())
    print("\n열 정보:")
    print(df.info())