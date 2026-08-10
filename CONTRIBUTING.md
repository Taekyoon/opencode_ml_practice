# Contributing to opencode_ml_practice

컨트리뷰션에 관심을 가져주셔서 감사합니다. 이 저장소는 OpenCode 기반 ML 튜토리얼이자
자율 연구 프레임워크입니다. 아래 가이드를 따라주세요.

## 시작하기

```bash
git clone https://github.com/Taekyoon/opencode_ml_practice.git
cd opencode_ml_practice
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.data_generation   # 학습용 가상 데이터 생성
```

## 개발 워크플로

- 작업 중 파일/태스크 구조는 [AGENTS.md](AGENTS.md)를 우선 따른다.
- 새 연구 태스크는 수동 생성하지 말고 스캐폴드 사용:
  ```bash
  make new-task TASK=<task_id> DATASET=<dataset_name> TARGET=<target_col>
  ```

## 테스트

```bash
make test        # python -m pytest tests/ -q
make wiki-lint   # 위키 지식 베이스 건강 검진 (broken link·고아·미등록)
```

커밋 전 반드시 통과 상태여야 합니다.

## 커밋 규칙

- `scripts/`, `research/tasks_registry.py`, `Makefile`, `research/wiki/`는 커밋 대상
- `research/**/results/`, `research/research.db`, `airflow/` 운영 산출물은 커밋 금지 (gitignore)
- 변경은 논리 단위로 나누고, 한 커밋에 하나의 변경을 담는다

## 버그 리포트 / 기능 제안

GitHub Issue에 아래를 포함해 작성해주세요:

1. 재현 방법 (명령어 포함)
2. 기대한 동작 vs 실제 동작
3. 환경 정보 (Python 버전, OS, 모델)

## 라이선스

MIT [LICENSE](LICENSE). 컨트리뷰션 제출은 MIT 라이선스 하에 배포되는 데 동의하는 것으로 간주합니다.