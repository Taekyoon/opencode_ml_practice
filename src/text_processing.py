"""텍스트 프롬프트를 수치 특성으로 바꾸는 전처리 모듈.

ML 모델은 문장을 직접 계산할 수 없으므로, 문장을 "특성 벡터"로 변환해야 한다.
여기서는 TF-IDF(Term Frequency × Inverse Document Frequency)를 사용한다.

- TF  : 한 문서에서 토큰이 얼마나 자주 나오는가 (빈도)
- IDF : 전체 문서에서 해당 토큰이 얼마나 희귀한가 (역문서빈도)
- TF-IDF = TF × IDF → 모든 문서에 나오는 흔한 단어(예: '알려줘')는 가중치가 낮아지고,
  특정 클래스에서만 나오는 단어(예: '시스템 프롬프트', 'DAN 모드')는 가중치가 높아진다.

한국어는 띄어쓰기를 기준으로 어절 단위 토큰을 만든다(형태소 분석기 불필요).
"""

import re

_NUM_ALPHA_KOR = re.compile(r"[0-9a-zA-Z가-힣]+")


def tokenize(text: str) -> list[str]:
    """문장을 소문자 토큰 list로 분해한다.

    한글은 어절(띄어쓰기 단위)로, 영문은 문자 단위로 떼어낸다.
    구두점/기호는 무시한다.
    """
    return [tok.lower() for tok in _NUM_ALPHA_KOR.findall(text or "")]


def build_tfidf_vectorizer(max_features: int = 2000, min_df: int = 1, max_df: float = 0.9):
    """TF-IDF Vectorizer 생성. tokenizer를 이 모듈의 tokenize로 고정한다."""
    from sklearn.feature_extraction.text import TfidfVectorizer

    return TfidfVectorizer(
        tokenizer=tokenize,
        token_pattern=None,
        lowercase=True,
        max_features=max_features,
        min_df=min_df,
        max_df=max_df,
    )


def fit_transform(texts: list[str], max_features: int = 2000):
    """문장 리스트 → TF-IDF 희소 행렬. 처음 학습(피팅)과 변환을 함께 한다."""
    vectorizer = build_tfidf_vectorizer(max_features=max_features)
    matrix = vectorizer.fit_transform(texts)
    return matrix, vectorizer


def transform(texts: list[str], vectorizer) -> "scipy.sparse_matrix":
    """이미 학습된 vectorizer로 새 문장 리스트를 변환한다. (실전 예측 시 사용)"""
    return vectorizer.transform(texts)


def top_feature_words(vectorizer, top_k: int = 10) -> list[str]:
    """학습된 vectorizer의 어휘 사전에서 상위 빈도 토큰 이름 몇 개를 반환한다."""
    vocab = vectorizer.vocabulary_
    if not vocab:
        return []
    return sorted(vocab, key=vocab.get)[:top_k]


if __name__ == "__main__":
    import pandas as pd

    df = pd.read_csv("data/prompt_dataset.csv")
    matrix, vec = fit_transform(df["text"].tolist())
    print(f"피팅 전 형태: {matrix.shape}")
    print(f"어휘 크기: {len(vec.vocabulary_)}")
    print(f"상위 빈도 토큰: {top_feature_words(vec)}")