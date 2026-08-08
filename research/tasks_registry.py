"""자율 ML 연구 태스크 레지스트리.

각 task는 research/<task_id>/ 폴더로 구성된다:
- program.md            : 연구 지침서 (사람이 작성)
- experiment_runner.py  : 에이전트가 수정하는 단일 파이프라인
- results/              : 실험 결과 (gitignore)
- reports/              : 일일 리포트 (gitignore)
- best_model/           : 최고 성능 모델 (gitignore)

DAG(ml_research_loop)는 이 레지스트리를 읽어 task별로 실험을 실행한다.
"""

import os
from dataclasses import dataclass

# 이 파일 위치: <루트>/research/tasks_registry.py
RESEARCH_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(RESEARCH_DIR)

DEFAULT_TASK = "failure_prediction"


@dataclass
class ExperimentTask:
    id: str                  # 폴더명 (레지스트리 키)
    kind: str                # classification | regression
    score_name: str          # 평가 지표 컬럼명
    runner: str              # runner 스크립트 경로 (프로젝트 루트 기준)
    program: str             # 지침서 경로 (프로젝트 루트 기준)
    results_dir: str         # 결과 폴더 경로 (프로젝트 루트 기준)
    description: str = ""    # 한 줄 설명


TASKS = {
    "failure_prediction": ExperimentTask(
        id="failure_prediction",
        kind="classification",
        score_name="score",           # F1 × PR-AUC
        runner="research/failure_prediction/experiment_runner.py",
        program="research/failure_prediction/program.md",
        results_dir="research/failure_prediction/results",
        description="반도체 failure 예측 (분류, 불균형 대응)",
    ),
    "quality_regression": ExperimentTask(
        id="quality_regression",
        kind="regression",
        score_name="r2",              # R²
        runner="research/quality_regression/experiment_runner.py",
        program="research/quality_regression/program.md",
        results_dir="research/quality_regression/results",
        description="제품 두께(thickness) 예측 (회귀)",
    ),
}


def get_task(task_id: str) -> ExperimentTask:
    """task_id(부분 일치 허용)로 등록된 태스크를 반환."""
    for key, task in TASKS.items():
        if key == task_id or (task_id and key.startswith(task_id)):
            return task
    raise KeyError(
        f"task '{task_id}'가 레지스트리에 없습니다. 등록된 task: {list(TASKS.keys())}"
    )


def list_tasks() -> list[str]:
    return sorted(TASKS.keys())


def get_all_tasks() -> list[ExperimentTask]:
    return [TASKS[t] for t in list_tasks()]


if __name__ == "__main__":
    print("[research] 등록된 태스크:")
    for t in get_all_tasks():
        print(f"  {t.id}: {t.description} (score={t.score_name})")