---
tags: [tasks, text_classification, prompt_security]
created: 2026-08-09
updated: 2026-08-10
task: prompt_guard
kind: classification
score_name: macro_f1 * pr_auc
dataset: prompt_dataset
target: label
---

# prompt_guard — 프롬프트 공격 탐지 가드레일 발견사항

> LLM 프롬프트를 5클래스(extraction/injection/jailbreak/manipulation/safe)로
> 다중 분류하는 가드레일 태스크. TF-IDF + LogisticRegression 파이프라인.
> 이 페이지는 실험에서 얻은 발견을 누적 기록한다.

## 현재 최고 결과

| run_id | score (F1×PR-AUC) | accuracy | hard_eval | 비고 |
|--------|--------------------|----------|-----------|------|
| run_20260810_090036 | **1.0** | 1.0 | 0.4242 (n=33) | 카테고리 분류, 하드 케이스 추가 평가 (J 모듈) |
| run_20260809_130315 | **1.0** | 1.0 | 0.4242 (n=33) | 카테고리 분류, 하드 케이스 평가 |

> **관찰**: 합성 `prompt_dataset`(1,500행, 5클래스 균형 잡기 좋은 분포)로는
> 분류가 완벽(score=1.0)하지만, **metalinguistic 하드 케이스**(공격 키워드를
> 인용/설명/테스트 문맥으로 말하는 문장)에서는 42%로 급락한다. 겉만 닮은
> 표면 단어 학습에 그쳐 어휘적 특징의 한계가 드러난다.

## 실행 이력

| run_id | score | accuracy | 비고 |
|--------|-------|----------|------|
| run_20260810_090036 | 1.0 | 1.0 | train/test 지표 + hard_eval (J2) |
| run_20260809_130315 | 1.0 | 1.0 | 하드 케이스 평가 추가 |
| run_20260809_124706 | 1.0 | 1.0 | 카테고리 분류만, hard 미평가 |
| (run_20260809_124641) | — | — | 실행 폴더만 생성, 결과 없음 |

## 발견 사항

- **합성 데이터 분포**: safe 750 / manipulation 210 / extraction·injection·jailbreak 180.
  TF-IDF(220 vocab) + LogisticRegression으로 train/test 모두 accuracy 1.0.
- **hard_eval이 진짜 실력**: 공격 문구를 "정의해줘/인용해줘/테스트에 포함해줘" 등
  중립적 맥락으로 요청한 문장은 safe로 분류해야 하는데 절반 이상을 공격으로
  오탐(hard acc 0.42). 특히 `injection`으로 몰리는 경향.
- **어휘 기반 한계**: `ignore all previous instructions` 같은 키워드 존재 여부만
  보고 판정하기 때문에, "해당 문구가 있는 로그를 분류해줘" 같은 문장도 공격으로 본다.

## 시도하지 않은 것 / 다음 후보

- [ ] 컨텍스트 인식: 문장 구조/목적어 자질(키워드가 실제 명령인지 인용인지) feature 추가
- [ ] 임베딩(SentenceTransformer 등) + 분류기 비교
- [ ] hard 케이스 오탐 줄이기: "인용/정의/설명" 맥락 문장을 safe로 유도하는 규칙 보강
- [ ] threshold/topic 분리: 다중 라벨 이진 분류기로 전환

## 교차 참조

- [datasets/lab_sensor_data.md](../datasets/lab_sensor_data.md) — 센서 데이터 (무관하나 위키 최초 진입점)
- [synthesis/lessons_learned.md](../synthesis/lessons_learned.md) — 교훈 종합