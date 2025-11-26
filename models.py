from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'teacher' or 'student'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    assignments = db.relationship("Assignment", backref="teacher", lazy=True)
    submissions = db.relationship("Submission", backref="student", lazy=True)

    def __repr__(self):
        return f"<User {self.email}>"


class Assignment(db.Model):
    __tablename__ = "assignments"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    submissions = db.relationship("Submission", backref="assignment", lazy=True)

    def __repr__(self):
        return f"<Assignment {self.title}>"


class Submission(db.Model):
    __tablename__ = "submissions"

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    text_response = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(255), nullable=True)

    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="submitted")  # submitted / graded
    plagiarism_score = db.Column(db.Float, default=0.0)  # 0-100 %

    feedback = db.relationship("Feedback", backref="submission", uselist=False)

    def __repr__(self):
        return f"<Submission assignment={self.assignment_id} student={self.student_id}>"


class Feedback(db.Model):
    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("submissions.id"), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    score = db.Column(db.Float, nullable=False)
    max_score = db.Column(db.Float, nullable=False)

    rubric_clarity = db.Column(db.Integer, nullable=False)      # 1-5
    rubric_completion = db.Column(db.Integer, nullable=False)   # 1-5
    rubric_presentation = db.Column(db.Integer, nullable=False) # 1-5

    comments = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher = db.relationship("User", backref="feedback_given", foreign_keys=[teacher_id])

    def __repr__(self):
        return f"<Feedback submission={self.submission_id} score={self.score}>"
