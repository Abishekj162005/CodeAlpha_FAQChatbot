import os
import logging

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from utils.db_helper import (
    db,
    init_db,
    get_all_faqs,
    add_faq,
    update_faq,
    delete_faq,
    record_feedback,
)
from utils.similarity import FAQMatcher


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)


# ============================================================
# CONFIGURATION
# ============================================================

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "faqbot-default-secret-key"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_DIR = os.path.join(BASE_DIR, "database")
DATABASE_PATH = os.path.join(DATABASE_DIR, "faq.db")

DATABASE_URI = os.getenv(
    "DATABASE_URI",
    f"sqlite:///{DATABASE_PATH.replace(os.sep, '/')}"
)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# ============================================================
# SIMILARITY THRESHOLD
# ============================================================

try:
    SIMILARITY_THRESHOLD = float(
        os.getenv("SIMILARITY_THRESHOLD", "0.45")
    )
except ValueError:
    logger.error("Invalid SIMILARITY_THRESHOLD value.")
    raise ValueError(
        "SIMILARITY_THRESHOLD must be a number between 0.0 and 1.0"
    )

if not 0.0 <= SIMILARITY_THRESHOLD <= 1.0:
    raise ValueError(
        "SIMILARITY_THRESHOLD must be between 0.0 and 1.0"
    )


# ============================================================
# FAQ SEED DATA
# ============================================================

SEED_JSON_PATH = os.path.join(
    BASE_DIR,
    "data",
    "faqs.json"
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

try:
    init_db(app, SEED_JSON_PATH)
    logger.info("Database initialized successfully.")
except Exception as e:
    logger.exception("Database initialization failed.")
    raise


# ============================================================
# FAQ NLP MATCHER
# ============================================================

matcher = None


def refresh_matcher():
    """
    Reload all FAQs and rebuild the TF-IDF similarity matcher.
    """

    global matcher

    with app.app_context():
        faqs = get_all_faqs()

        matcher = FAQMatcher(
            faqs,
            threshold=SIMILARITY_THRESHOLD
        )

        logger.info(
            "FAQ Matcher refreshed with %d FAQs.",
            len(faqs)
        )


try:
    refresh_matcher()
except Exception as e:
    logger.exception("FAQ Matcher initialization failed.")
    raise


# ============================================================
# MAIN PAGE
# ============================================================

@app.route("/")
def index():
    """
    Render the main FAQBot interface.
    """

    return render_template("index.html")


# ============================================================
# ASK QUESTION
# ============================================================

@app.route("/ask", methods=["POST"])
def ask():
    """
    FAQ question answering API.

    Request:
    {
        "question": "How can I track my order?"
    }
    """

    try:

        data = request.get_json(silent=True) or {}

        user_question = data.get("question", "")

        if not isinstance(user_question, str):
            return jsonify({
                "status": "error",
                "message": "Question must be a string.",
                "answer": "Please enter a valid question.",
                "matched": False,
                "similarity": 0.0
            }), 400

        user_question = user_question.strip()

        # ----------------------------------------------------
        # EMPTY QUESTION
        # ----------------------------------------------------

        if not user_question:
            suggestions = []

            if matcher:
                try:
                    suggestions = matcher._get_default_suggestions()
                except Exception:
                    suggestions = []

            return jsonify({
                "status": "error",
                "message": "Please enter a valid question.",
                "answer": "Please enter a question so I can help you!",
                "matched": False,
                "similarity": 0.0,
                "suggestions": suggestions
            }), 400

        # ----------------------------------------------------
        # MAXIMUM QUESTION LENGTH
        # ----------------------------------------------------

        if len(user_question) > 500:
            return jsonify({
                "status": "error",
                "message": "Question must not exceed 500 characters.",
                "answer": "Please shorten your question to 500 characters or less.",
                "matched": False,
                "similarity": 0.0
            }), 400

        # ----------------------------------------------------
        # MATCHER CHECK
        # ----------------------------------------------------

        if matcher is None:
            logger.error("FAQ matcher is not initialized.")

            return jsonify({
                "status": "error",
                "message": "FAQ matcher is unavailable.",
                "answer": "The FAQ service is temporarily unavailable.",
                "matched": False,
                "similarity": 0.0
            }), 500

        # ----------------------------------------------------
        # FIND BEST MATCH
        # ----------------------------------------------------

        result = matcher.find_best_match(user_question)

        return jsonify({
            "status": "success",
            "question": user_question,
            "answer": result.get("answer", ""),
            "matched": result.get("matched", False),
            "similarity": result.get("similarity", 0.0),
            "faq": result.get("faq"),
            "suggestions": result.get("suggestions", [])
        }), 200

    except Exception as e:

        logger.exception("Error while processing question.")

        return jsonify({
            "status": "error",
            "message": "An internal server error occurred.",
            "answer": "Sorry, something went wrong. Please try again.",
            "matched": False,
            "similarity": 0.0
        }), 500


# ============================================================
# GET ALL FAQS
# ============================================================

@app.route("/api/faqs", methods=["GET"])
def get_faqs():

    try:

        faqs = get_all_faqs()

        return jsonify({
            "status": "success",
            "faqs": faqs,
            "count": len(faqs)
        }), 200

    except Exception as e:

        logger.exception("Failed to load FAQs.")

        return jsonify({
            "status": "error",
            "message": "Unable to load FAQs."
        }), 500


# ============================================================
# CREATE FAQ
# ============================================================

@app.route("/api/faqs", methods=["POST"])
def create_faq():

    try:

        data = request.get_json(silent=True) or {}

        question = data.get("question", "")
        answer = data.get("answer", "")
        category = data.get("category", "General")

        if not isinstance(question, str):
            question = ""

        if not isinstance(answer, str):
            answer = ""

        if not isinstance(category, str):
            category = "General"

        question = question.strip()
        answer = answer.strip()
        category = category.strip() or "General"

        if not question or not answer:
            return jsonify({
                "status": "error",
                "message": "Both question and answer are required."
            }), 400

        if len(question) > 500:
            return jsonify({
                "status": "error",
                "message": "Question must not exceed 500 characters."
            }), 400

        new_faq = add_faq(
            question,
            answer,
            category
        )

        refresh_matcher()

        return jsonify({
            "status": "success",
            "faq": new_faq,
            "message": "FAQ added successfully."
        }), 201

    except Exception as e:

        logger.exception("Failed to create FAQ.")

        return jsonify({
            "status": "error",
            "message": "Unable to create FAQ."
        }), 500


# ============================================================
# UPDATE FAQ
# ============================================================

@app.route("/api/faqs/<int:faq_id>", methods=["PUT"])
def edit_faq(faq_id):

    try:

        data = request.get_json(silent=True) or {}

        question = data.get("question")
        answer = data.get("answer")
        category = data.get("category")

        if isinstance(question, str):
            question = question.strip()

        if isinstance(answer, str):
            answer = answer.strip()

        if isinstance(category, str):
            category = category.strip()

        updated = update_faq(
            faq_id,
            question=question,
            answer=answer,
            category=category
        )

        if not updated:
            return jsonify({
                "status": "error",
                "message": "FAQ not found."
            }), 404

        refresh_matcher()

        return jsonify({
            "status": "success",
            "faq": updated,
            "message": "FAQ updated successfully."
        }), 200

    except Exception as e:

        logger.exception("Failed to update FAQ.")

        return jsonify({
            "status": "error",
            "message": "Unable to update FAQ."
        }), 500


# ============================================================
# DELETE FAQ
# ============================================================

@app.route("/api/faqs/<int:faq_id>", methods=["DELETE"])
def remove_faq(faq_id):

    try:

        success = delete_faq(faq_id)

        if not success:
            return jsonify({
                "status": "error",
                "message": "FAQ not found."
            }), 404

        refresh_matcher()

        return jsonify({
            "status": "success",
            "message": "FAQ deleted successfully."
        }), 200

    except Exception as e:

        logger.exception("Failed to delete FAQ.")

        return jsonify({
            "status": "error",
            "message": "Unable to delete FAQ."
        }), 500


# ============================================================
# GET CATEGORIES
# ============================================================

@app.route("/api/categories", methods=["GET"])
def get_categories():

    try:

        faqs = get_all_faqs()

        categories = sorted(
            list({
                faq.get("category", "General")
                for faq in faqs
            })
        )

        return jsonify({
            "status": "success",
            "categories": categories
        }), 200

    except Exception as e:

        logger.exception("Failed to load categories.")

        return jsonify({
            "status": "error",
            "message": "Unable to load categories."
        }), 500


# ============================================================
# FEEDBACK
# ============================================================

@app.route("/api/feedback", methods=["POST"])
def feedback():

    try:

        data = request.get_json(silent=True) or {}

        user_question = data.get("question", "")
        helpful = data.get("helpful", True)
        faq_id = data.get("faq_id")

        if not isinstance(user_question, str):
            user_question = ""

        user_question = user_question.strip()

        if not isinstance(helpful, bool):
            helpful = bool(helpful)

        result = record_feedback(
            user_question,
            helpful,
            faq_id
        )

        return jsonify({
            "status": "success",
            "feedback": result
        }), 200

    except Exception as e:

        logger.exception("Failed to record feedback.")

        return jsonify({
            "status": "error",
            "message": "Unable to record feedback."
        }), 500


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/api/health", methods=["GET"])
def health():

    try:

        faq_count = len(get_all_faqs())

        return jsonify({
            "status": "healthy",
            "faq_count": faq_count,
            "similarity_threshold": SIMILARITY_THRESHOLD
        }), 200

    except Exception as e:

        logger.exception("Health check failed.")

        return jsonify({
            "status": "unhealthy",
            "faq_count": 0,
            "similarity_threshold": SIMILARITY_THRESHOLD
        }), 500


# ============================================================
# LOCAL DEVELOPMENT
# ============================================================

if __name__ == "__main__":

    port = int(
        os.getenv("PORT", "5000")
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )