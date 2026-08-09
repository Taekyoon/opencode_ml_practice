# prompt_guard — 자율 연구 지침서

> 프롬프트 공격 탐지 가드레일 태스크. LLM 사용자 프롬프트의 안전성을 판별한다.
> - 데이터셋: `prompt_dataset` (합성 프롬프트 1,500건, text label 컬럼)
> - 목표 변수: `label`  (safe / injection / jailbreak / extraction / manipulation)
> - 태스크 종류: **다중 클래스 텍스트 분류**

## 1. 배경

실서비스에 LLM을 붙이면, 사용자는 모델을 "내 맘대로" 만들려는 공격 프롬프트를 보낸다.
프롬프트 인젝션, 제약 해제(jailbreak), 시스템 프롬프트 탈취, 사실/출력 조작 등이 대표적이다.
이 태스크는 **들어오는 프롬프트를 안전성 관점에서 등급 분류**하는 가드레일 모델을 만든다.

## 2. 데이터 성격

- `text`: 사용자 프롬프트 (한국어/영어 혼합)
- `label`: 5개 클래스. 합성 데이터라 **분포는 균형적**(safe 50%)이다.
  실전에서는 safe 가 95% 이상일 수 있으니, 불균형 상황까지 함께 고민한다.
- `src/generate_prompt_data.generate_hard_prompts()` 의 **경계 사례**(하드 케이스)는
  오탐/위장 공격을 재현한다. 실행 메인 비교보다 이 쪽이 실제 방어 난이도를 보여준다.

## 3. 평가 지표

- 분류 기준 점수: `score = F1(macro) × PR-AUC(macro)`
- 보조 지표: accuracy, 클래스별 precision/recall/F1, 하드 케이스 정확도
- **하드 케이스 정확도가 낮게 유지되면 성능이 좋아도 실전에 부적합**하다.

## 4. 반복 전략 (A/B 원칙)

1. 과거 결과 먼저 확인 (`research/prompt_guard/results/`)
2. 한 번에 하나의 변수만 변경 (모델 유형, vectorizer 설정, 클래스 가중치 등)
3. 개선되면 keep, 아니면 되돌리기
4. 오탐(false positive · 즉 safe를 공격으로 분류)을 최소화하는 방향을 우선한다 —
   정상 사용자를 차단하면 서비스 품질이 나빠진다.

## 5. 실행

- 로컬: `python research/prompt_guard/experiment_runner.py`
- Airflow: 연구 에이전트가 자동 실행