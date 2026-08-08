# A3. 데이터 이해 — 반도체 공정 데이터란?

## 학습 목표
- 생성된 가상 데이터의 열(변수) 하나하나의 의미를 이해한다
- 불량(failure) 라벨이 어떻게 만들어졌는지 안다
- 데이터의 분포를 실제로 탐색한다

## 배경 지식: 이 데이터는 무엇인가?

반도체 웨이퍼를 만들 때 수많은 **공정 단계**(온도 가열, 압력, 식각, 증착...)를 거친다.
각 단계마다 **센서**가 온도·압력·시간 등을 측정하고, 마지막에 **검사 단계**에서
제품이 불량(failure)인지 판정한다.

이 프로젝트의 `src/data_generation.py`는 이 과정을 **가상으로** 흉내 낸 데이터를 만든다.
실제 센서 데이터가 없어도 파이프라인을 개발/학습할 수 있게 하기 위함이다.

### 열(변수) 설명

| 열 | 의미 | 단위 | 생성 방식 |
|----|------|------|-----------|
| `temperature` | 공정 온도 | °C | 20~300 균등분포 |
| `pressure` | 공정 압력 | atm | 1~10 균등분포 |
| `process_time` | 공정 시간 | min | 1~60 균등분포 |
| `chemical_concentration` | 화학물 농도 | M | 0.1~10 균등분포 |
| `thickness` | 측정된 막 두께 | (임의) | 온도·압력에 의존 + 노이즈 |
| `resistivity` | 측정된 저항률 | (임의) | 온도에 의존 + 노이즈 |
| `dopant` | 도펀트 농도 | (임의) | 농도에 의존 + 노이즈 |
| `failure` | 불량 여부 (라벨) | 0/1 | 로짓 확률 기반 |

> **관찰**: 공정 변수(위 4개)는 "설정값", 측정 변수(중간 3개)는 "공정 결과로 나온 값",
> 라벨(마지막)은 "판정 결과"다. 예측 모델은 첫 7개로 `failure`를 맞히는 것이 목표다.

## 따라하기

### 1단계: 데이터 생성 스크립트 다시 보기
`src/data_generation.py`의 주석을 읽는다.
```bash
python -c "import inspect, src.data_generation as d; print(inspect.getdoc(d.generate_synthetic_data))"
```

### 2단계: 라벨이 만들어지는 원리 (logit)
`src/data_generation.py` 40~50행을 보면:
```python
logit = (
    -10.5
    + 0.8 * (temperature - 150.0) / 80.0
    - 1.2 * (pressure - 5.5) / 2.5
    ...
)
prob_failure = 1.0 / (1.0 + np.exp(-logit))
```

- **logit** = 각 변수가 불량 확률에 주는 영향의 합 (양수 → 불량 확률 ↑)
- `1.0 / (1.0 + exp(-logit))` = **시그모이드**. 어떤 값이든 0~1 확률로 바꿔준다
- 온도가 높을수록(+0.8), 압력이 낮을수록(-1.2) 불량 확률이 올라간다

> 이것은 "실제 물리 법칙"이 아니라 **가상 시나리오**다.
> 하지만 "여러 변수가 확률에 기여하고, 확률로 라벨이 정해진다"는 구조는
> 실제 반도체 결함 분석에서도 동일하다.

### 3단계: 데이터 분포 탐색
```bash
python - <<'PY'
import pandas as pd
df = pd.read_csv("data/synthetic_data.csv")
print(df.describe().round(2))
print("\n불량률:", df["failure"].mean().round(4))
print("불량 수:", df["failure"].sum(), "/", len(df))
PY
```

### 4단계: 불량과 정상의 차이 (단순 관찰)
```bash
python - <<'PY'
import pandas as pd
df = pd.read_csv("data/synthetic_data.csv")
ok = df[df["failure"] == 0]
bad = df[df["failure"] == 1]
print("정상 온도 평균:", round(ok["temperature"].mean(), 1))
print("불량 온도 평균:", round(bad["temperature"].mean(), 1))
print("정상 압력 평균:", round(ok["pressure"].mean(), 2))
print("불량 압력 평균:", round(bad["pressure"].mean(), 2))
PY
```
불량이 온도가 높고 압력이 낮은 쪽에 몰려 있는지 확인한다.

## 이해 확인

1. 공정 변수와 측정 변수의 차이는 무엇인가?
2. 시그모이드 함수는 어떤 역할을 하는가?
3. 불량률은 약 몇 %인가? 이 수치가 모델 학습에 어떤 영향을 줄까?

## opencode에게 물어보세요

```
data/synthetic_data.csv를 분석해서 각 변수의 분포와 상관관계를 요약해줘.
불량(failure)을 예측하는데 가장 영향력이 커 보이는 변수는 뭐야?
```

## 다음 레슨
[A4. opencode 시작하기](04_opencode_introduction.md) — 이 프로젝트에서 AI 코딩 도구를 쓰는 법.