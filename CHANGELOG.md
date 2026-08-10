# Changelog

이 저장소의 주요 변경을 기록한다. 버전과 커밋 해시 기준.

## v0.1.0 — 2026-08-10 공개 스냅샷

A~J 모듈 33개 레슨이 완성된 상태를 처음으로 고정한 공개 스냅샷.

### 오픈소스 공개 준비
- **LICENSE** 추가 — MIT (`(c) 2026 Taekyoon`)
- **README** 하단에 라이선스·인용 섹션 추가
  - WM-811K(CC0) 원본 논문 인용: Wu, Jang & Chen (2015), IEEE TSM 28(1), DOI 10.1109/TSM.2014.2364237
  - 개념 차용: Shepherd/SkillOpt(Karpathy LLM Wiki)
  - 도구: opencode, Apache Airflow, scikit-learn, imbalanced-learn
- **README** AI 생성 코드 공개 문구 추가 (opencode/deepseek-v4-flash-free 기반 작성 명시)
- **CONTRIBUTING.md** 신설 (개발 워크플로·테스트·커밋 규칙·버그 리포트)
- **CODE_OF_CONDUCT.md** 신설 (Contributor Covenant 2.1)
- **저장소 전체 개인정보 제거**
  - `archive/docs/RETROSPECTIVE.md` 로컬 경로 마스킹
  - `docs/design/INSTALL_LOG.md` 로컬 경로 마스킹
  - `notebooks/semiconductor_failure_analysis.ipynb` 출력 셀 로컬 경로 마스킹
- **데이터셋 위키 보강**
  - `research/wiki/datasets/wm811k.md` — 논문 인용·CC0 배포·다운로드 절차 명시
  - `research/wiki/datasets/lab_sensor_data.md` — 합성 데이터 라이선스·재생성 방법 명시

## v0.0.x~v0.1.0 진화 과정 (2026-08-08 ~ 08-10)

### 튜토리얼 본체 (A~J)
- A~J 모듈 33개 레슨 작성 · 수료 기준(모듈 F) 정의
- 모듈 J(에이전트 발전 심화) 인프라·레슨 추가 — 이벤트 기록, 검증 게이트,
  제안→검증→적용 루프 (Shepherd/SkillOpt 개념 차용, 런타임 의존성 없음)
- 엔지니어링 개념 문서 `docs/design/ENGINEERING_CONCEPTS.md` 신설
- 에이전트 프레임워크 분석 문서 `docs/design/AGENT_FRAMEWORKS_ANALYSIS.md` +
  설치 로그 `docs/design/INSTALL_LOG.md`

### 품질 보정 (P0/P1/P2 검토)
- P0 3건: fresh clone 실행성 복구
- P1 12건: 출력 예 실측화·린트/롤백·용어·링크 보정
- P2 11건: 태스크 개수 4개 동일화·이미지 등록 절차·스킬 import·역링크·오타·시간 표기
- 방안 2: D2/E3/J3 엔지니어링 관점(하네스·루프·그래프 공학) 스포트라이트 추가
- 출력 예 실측 동기화(C2/B4)·위키 실행 횟수/최고 결과 DB 정합

### 인프라/코드
- 검증 게이트 `src/validation_gate.py` + 유닛 테스트 + `make test` 타겟
- 레거시(초기 실험 스위트·대화 로그) `archive/`로 이동 + Makefile 타겟 정리
- `research/wiki` DAG 실행 ingest 기록 (4개 태스크)

### 데이터셋
- WM-811K 로더 `src/wafer_data_loader.py` (공개 데이터셋, gitignore로 데이터 제외)
- 웨이퍼맵 이미지 생성/분류 태스크(`wafer_vision`), 프롬프트 가드레일(`prompt_guard`) 추가