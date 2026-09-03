"""
TF-IDF based keyword matching using scikit-learn.
"""
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine

logger = logging.getLogger(__name__)


def compute_tfidf_similarity(text_a: str, text_b: str) -> float:
    """
    Compute TF-IDF cosine similarity between two texts.
    Returns a float between 0.0 and 1.0.
    """
    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=5000,
            ngram_range=(1, 2),  # Unigrams + bigrams for better matching
            sublinear_tf=True,
        )
        tfidf_matrix = vectorizer.fit_transform([text_a, text_b])
        similarity = sklearn_cosine(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(similarity)
    except Exception as e:
        logger.warning(f"TF-IDF computation failed: {e}")
        return 0.0


def compute_tfidf_batch(reference_text: str, candidate_texts: list[str]) -> list[float]:
    """
    Compute TF-IDF similarity of a reference text against multiple candidates.
    More efficient than calling compute_tfidf_similarity in a loop.
    """
    try:
        all_texts = [reference_text] + candidate_texts
        vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=5000,
            ngram_range=(1, 2),
            sublinear_tf=True,
        )
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        similarities = sklearn_cosine(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
        return [float(s) for s in similarities]
    except Exception as e:
        logger.warning(f"Batch TF-IDF computation failed: {e}")
        return [0.0] * len(candidate_texts)
