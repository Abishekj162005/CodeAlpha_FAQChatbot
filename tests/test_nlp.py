import unittest
from utils.preprocessing import preprocess_text, clean_text
from utils.similarity import FAQMatcher

class TestNLPPreprocessing(unittest.TestCase):
    def test_clean_text(self):
        sample = "How CAN I track my ORDER???"
        cleaned = clean_text(sample)
        self.assertEqual(cleaned, "how can i track my order")

    def test_preprocess_text(self):
        sample = "How CAN I track my ORDER???"
        processed = preprocess_text(sample)
        self.assertIn("track", processed)
        self.assertIn("order", processed)
        # Verify punctuation and stopwords were handled
        self.assertNotIn("?", processed)
        self.assertNotIn("how", processed)


class TestFAQMatcher(unittest.TestCase):
    def setUp(self):
        self.faqs = [
            {
                "id": 1,
                "category": "Account",
                "question": "How can I reset my password?",
                "answer": "Click Forgot Password on the login page."
            },
            {
                "id": 2,
                "category": "Orders",
                "question": "How can I track my order?",
                "answer": "Open My Orders and select the order you want to track."
            },
            {
                "id": 3,
                "category": "Payments",
                "question": "What payment methods are supported?",
                "answer": "We support credit cards, debit cards, UPI and net banking."
            }
        ]
        self.matcher = FAQMatcher(self.faqs, threshold=0.40)

    def test_exact_match(self):
        res = self.matcher.find_best_match("How can I reset my password?")
        self.assertTrue(res["matched"])
        self.assertEqual(res["faq"]["id"], 1)
        self.assertGreaterEqual(res["similarity"], 0.90)

    def test_rephrased_match(self):
        res = self.matcher.find_best_match("I lost password how to change it?")
        self.assertTrue(res["matched"])
        self.assertEqual(res["faq"]["id"], 1)

    def test_fallback_unrelated(self):
        res = self.matcher.find_best_match("Do you sell sports cars?")
        self.assertFalse(res["matched"])
        self.assertLess(res["similarity"], 0.40)
        self.assertIn("couldn't find a relevant answer", res["answer"])


if __name__ == "__main__":
    unittest.main()
