# C4. 위키 검진 — wiki_lint로 건강 상태 확인

## 학습 목표
- 위키가 "깨진 상태"가 될 수 있음을 안다
- `make wiki-lint`(=`scripts/wiki_lint.py`)가 검사하는 4가지를 이해한다
- 실제로 실행해보고 결과를 해석한다

## 배경 지식

### 위키가 망가지는 이유
LLM이 위키를 만들다 보면 이런 일이 생긴다:
- 만든 페이지를 `index.md`에 등록 안 함 → **사람/LLM이 못 찾음**
- 어떤 페이지도 링크하지 않음 → **고아 페이지**
- 다른 페이지로 링크했는데 그 파일이 사라짐 → **broken link**
- 갱신이 오래된 페이지 → **정보가 낡음**

`scripts/wiki_lint.py`가 이 4가지를 자동 검사한다.

### 검사 항목 표

| 번호 | 검사 | 조건 |
|------|------|------|
| 1 | index 미등록 | wiki/의 모든 .md가 index.md에 링크되어 있는가 |
| 2 | 고아 페이지 | 다른 페이지가 링크하지 않는가 (index/log 제외) |
| 3 | broken 링크 | 내부 `(xxx.md)` 링크의 파일이 있는가 |
| 4 | 오래된 데이터 | frontmatter `updated`가 7일 이상 지났는가 |

## 따라하기

### 1단계: 실행
```bash
make wiki-lint
```
(또는 직접: `python scripts/wiki_lint.py`)

### 2단계: 출력 해석
```
wiki 린트 결과: 0 개 문제 발견
오래된 데이터 (7일+ 미갱신):
```
- "문제 없음"이 나오면 정상
- 오래된 데이터 항목이 보이면 실제로 위키에 낡은 페이지일 가능성 — 갱신 대상

### 3단계: 일부러 문제 만들기 (연습)
```bash
echo "# temp" > research/wiki/temp_page.md       # 1) index에 없음 → 미등록
echo "[]" > research/wiki/index_tmp_broken.md
```
린트 재실행:
```bash
python scripts/wiki_lint.py
```
`[미등록] temp_page.md`가 잡히는 것을 확인한다.

### 4단계: 정리
```bash
rm research/wiki/temp_page.md
make wiki-lint
```
다시 문제 없음을 확인한다.

## 이해 확인

1. 이 4가지 검사 중 실무에서 가장 흔한 것은 (또는 가장 해로운 것은) 무엇인가?
2. `updated` frontmatter가 없다면 4번 검사에서 어떻게 되는가? (통과)
3. 린트가 문제를 1개라도 발견하면 종료 코드는 몇인가? (1)

## opencode에게 물어보세요
```
scripts/wiki_lint.py의 고아 페이지 검사를 실행으로 수행해보고,
지금 위키에 고아 페이지가 있는지 확인해줘.
```

## 다음 레슨
[모듈 D 시작하기](../D_infrastructure/15_airflow_basics.md) — Airflow로 실행을 자동화한다.