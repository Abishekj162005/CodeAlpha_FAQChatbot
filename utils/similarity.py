import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from utils.preprocessing import preprocess_text
import logging

logger = logging.getLogger(__name__)

FALLBACK_RESPONSE = (
    "I'm sorry, I couldn't find a relevant answer to your question. "
    "Please try rephrasing your question or select one of the popular FAQs below."
)

class FAQMatcher:
    def __init__(self, faqs: list, threshold: float = 0.40):
        """
        Initializes FAQMatcher with a list of FAQ dictionaries.
        Each FAQ dictionary must contain: id, question, answer, category.
        """
        self.threshold = threshold
        self.faqs = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self.processed_questions = []
        self.update_faqs(faqs)

    def update_faqs(self, faqs: list):
        """
        Updates the FAQ knowledge base and rebuilds the TF-IDF matrix.
        """
        self.faqs = faqs
        if not self.faqs:
            self.vectorizer = None
            self.tfidf_matrix = None
            self.processed_questions = []
            return

        # Preprocess all FAQ questions
        self.processed_questions = [
            preprocess_text(faq["question"]) for faq in self.faqs
        ]

        # Handle edge case where preprocessing results in empty strings
        non_empty_corpus = [q if q else faq["question"].lower() for q, faq in zip(self.processed_questions, self.faqs)]

        # Fit TF-IDF Vectorizer
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True
        )
        try:
            self.tfidf_matrix = self.vectorizer.fit_transform(non_empty_corpus)
            logger.info(f"TF-IDF Vectorizer successfully trained on {len(self.faqs)} FAQs.")
        except Exception as e:
            logger.error(f"Error fitting TfidfVectorizer: {e}")
            self.tfidf_matrix = None

    def find_best_match(self, query: str, threshold: float = None) -> dict:
        """
        Calculates cosine similarity between user query vector and all FAQ vectors.
        Returns dictionary with match results, similarity score, and suggested FAQs.
        """
        if threshold is None:
            threshold = self.threshold

        if not query or not query.strip():
            return {
                "matched": False,
                "answer": "Please enter a valid question.",
                "similarity": 0.0,
                "faq": None,
                "suggestions": self._get_default_suggestions()
            }

        if not self.faqs or self.tfidf_matrix is None or self.vectorizer is None:
            return {
                "matched": False,
                "answer": FALLBACK_RESPONSE,
                "similarity": 0.0,
                "faq": None,
                "suggestions": []
            }

        # Step 1: Preprocess user query
        processed_query = preprocess_text(query)
        if not processed_query:
            processed_query = query.lower()

        # Step 2: Convert query to TF-IDF vector
        query_vector = self.vectorizer.transform([processed_query])

        # Step 3: Compute Cosine Similarity against all FAQ vectors
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()

        if len(similarities) == 0:
            return {
                "matched": False,
                "answer": FALLBACK_RESPONSE,
                "similarity": 0.0,
                "faq": None,
                "suggestions": self._get_default_suggestions()
            }

        # Step 4: Find highest similarity score index
        best_idx = int(np.argmax(similarities))
        best_score = float(similarities[best_idx])

        # Step 5: Check against threshold
        if best_score >= threshold:
            best_faq = self.faqs[best_idx]
            return {
                "matched": True,
                "answer": best_faq["answer"],
                "similarity": round(best_score, 4),
                "faq": best_faq,
                "suggestions": self._get_related_suggestions(best_idx, similarities)
            }
        else:
            return {
                "matched": False,
                "answer": FALLBACK_RESPONSE,
                "similarity": round(best_score, 4),
                "faq": None,
                "suggestions": self._get_top_suggestions(similarities, top_n=4)
            }

    def _get_default_suggestions(self, count: int = 4) -> list:
        """Returns default suggestions from the FAQ list."""
        return [faq["question"] for faq in self.faqs[:count]]

    def _get_top_suggestions(self, similarities: np.ndarray, top_n: int = 4) -> list:
        """Returns top N questions sorted by similarity score."""
        sorted_indices = np.argsort(similarities)[::-1]
        suggestions = []
        for idx in sorted_indices[:top_n]:
            if idx < len(self.faqs):
                suggestions.append(self.faqs[idx]["question"])
        return suggestions if suggestions else self._get_default_suggestions(top_n)

    def _get_related_suggestions(self, current_idx: int, similarities: np.ndarray, count: int = 3) -> list:
        """Returns related suggestions excluding the matched question."""
        sorted_indices = np.argsort(similarities)[::-1]
        related = []
        for idx in sorted_indices:
            if idx != current_idx and idx < len(self.faqs):
                related.append(self.faqs[idx]["question"])
                if len(related) >= count:
                    break
        return related if related else self._get_default_suggestions(count)
