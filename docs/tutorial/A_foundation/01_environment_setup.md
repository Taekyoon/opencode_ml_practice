# A1. 환경 세팅 — 프로젝트를 처음 실행해보기

## 학습 목표
- Python이 설치되어 있는지 확인한다
- 가상환경(`.venv`)과 `pip`의 역할을 이해한다
- 이 프로젝트의 첫 번째 명령을 실행한다

## 배경 지식

### Python, pip, 가상환경
| 용어 | 설명 |
|------|------|
| **Python** | 코드를 해석하고 실행하는 프로그래밍 언어 |
| **pip** | Python 패키지를 설치하는 도구 (예: `pip install numpy`) |
| **가상환경** (`venv`) | 프로젝트마다 독립된 패키지 모음을 만들어 주는 것. 다른 프로젝트와 충돌을 막는다 |
| **requirements.txt** | 프로젝트가 필요로 하는 패키지 목록이 적힌 파일 |

> **왜 가상환경이 필요한가?**
> 프로젝트 A가 numpy 1.x를 쓰고, 프로젝트 B가 numpy 2.x를 쓴다고 가정하자.
> 전역에 설치하면 한쪽이 깨진다. 가상환경은 각 프로젝트에 "자기만의 Python 세상"을 만들어 준다.

## 따라하기

### 1단계: Python 버전 확인
터미널에서 다음을 실행한다:

```bash
python3 --version
```

출력 예:
```
Python 3.12.4
```

> **중요**: 이 프로젝트는 Python **3.10 이상**이 필요하다.
> 아래 코드에서 `str | None` 같은 문법(유니언 타입)이 3.10에서 도입되었기 때문이다.
>
> ```
> # src/data_manager.py  (예시)
> def register_file(filename: str, note: str | None = None):
> ```

### 2단계: 프로젝트 폴더로 이동
```bash
cd ~/opencode_ml_practice
```
> `cd`는 "change directory"(폴더 이동)의 약자다.
> `ls`를 입력하면 폴더 안에 무엇이 있는지 볼 수 있다.

### 3단계: 가상환경 만들기
```bash
python3 -m venv .venv
```
`.venv`라는 폴더가 생성된다. 여기에 이 프로젝트 전용 Python과 패키지가 들어간다.

### 4단계: 가상환경 활성화
```bash
source .venv/bin/activate
```
프롬프트 앞에 `(.venv)`가 붙으면 성공이다.

### 5단계: 패키지 설치
```bash
pip install -r requirements.txt
```

### 6단계: 프로젝트의 첫 실행
이 프로젝트는 가상 반도체 공정 데이터를 생성하는 스크립트를 제공한다.
```bash
python -m src.data_generation
```
`data/synthetic_data.csv` 파일이 생성된다.

확인:
```bash
ls data/
```
출력 예:
```
synthetic_data.csv
```

### 7단계: 데이터 확인
```bash
python -c "import pandas as pd; df = pd.read_csv('data/synthetic_data.csv'); print(df.shape); print(df.head())"
```
```
(5000, 8)
   temperature  pressure  ...
```

## 이해 확인

1. 가상환경은 왜 필요한가?
2. `python -m src.data_generation`에서 `-m`은 무엇을 의미하는가? (힌트: 모듈)
3. `requirements.txt`를 열어 어떤 패키지들이 들어있는지 확인해보자.

## opencode에게 물어보세요

```
이 프로젝트의 requirements.txt를 설명해줘. 각 패키지가 어떤 역할을 하는지.
```

> 참고: 이 레슨 이후부터 생성되는 파일들(`data/synthetic_data.csv`)은 `.gitignore`에 의해
> 버전 관리에서 제외된다. 팀원이 새로 clone하면 다시 만들어야 하므로, 레슨 시작 전에
> 데이터가 없으면 이 명령을 먼저 실행하자:
> ```bash
> python -m src.data_generation
> ```

## 다음 레슨
[A2. 프로젝트 둘러보기](02_project_walkthrough.md) — 이 프로젝트의 전체 구조를 파악한다.