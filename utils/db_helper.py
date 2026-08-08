import os
import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import logging

logger = logging.getLogger(__name__)

db = SQLAlchemy()

class FAQ(db.Model):
    __tablename__ = 'faqs'

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False, default='General')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Feedback(db.Model):
    __tablename__ = 'feedback'

    id = db.Column(db.Integer, primary_key=True)
    faq_id = db.Column(db.Integer, db.ForeignKey('faqs.id'), nullable=True)
    user_question = db.Column(db.Text, nullable=False)
    helpful = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "faq_id": self.faq_id,
            "user_question": self.user_question,
            "helpful": self.helpful,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


def init_db(app, json_seed_path: str = None):
    """
    Initializes SQLAlchemy database and seeds data if empty.
    """
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if "sqlite:///" in db_uri:
        raw_path = db_uri.split("sqlite:///")[-1]
        db_path = os.path.abspath(raw_path)
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"Created database directory: {db_dir}")

    db.init_app(app)

    with app.app_context():
        db.create_all()

        # Seed data if table is empty
        if FAQ.query.count() == 0:
            if json_seed_path and os.path.exists(json_seed_path):
                logger.info(f"Seeding FAQs from {json_seed_path}...")
                try:
                    with open(json_seed_path, 'r', encoding='utf-8') as f:
                        faq_list = json.load(f)
                        for item in faq_list:
                            faq = FAQ(
                                question=item['question'],
                                answer=item['answer'],
                                category=item.get('category', 'General')
                            )
                            db.session.add(faq)
                        db.session.commit()
                        logger.info(f"Successfully seeded {len(faq_list)} FAQs into SQLite database.")
                except Exception as e:
                    logger.error(f"Error seeding database: {e}")
                    db.session.rollback()


def get_all_faqs():
    return [faq.to_dict() for faq in FAQ.query.all()]


def add_faq(question: str, answer: str, category: str = 'General'):
    faq = FAQ(question=question, answer=answer, category=category)
    db.session.add(faq)
    db.session.commit()
    return faq.to_dict()


def update_faq(faq_id: int, question: str = None, answer: str = None, category: str = None):
    faq = FAQ.query.get(faq_id)
    if not faq:
        return None
    if question is not None:
        faq.question = question
    if answer is not None:
        faq.answer = answer
    if category is not None:
        faq.category = category
    db.session.commit()
    return faq.to_dict()


def delete_faq(faq_id: int):
    faq = FAQ.query.get(faq_id)
    if not faq:
        return False
    db.session.delete(faq)
    db.session.commit()
    return True


def record_feedback(user_question: str, helpful: bool, faq_id: int = None):
    fb = Feedback(user_question=user_question, helpful=helpful, faq_id=faq_id)
    db.session.add(fb)
    db.session.commit()
    return fb.to_dict()
