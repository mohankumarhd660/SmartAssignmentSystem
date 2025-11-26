import os
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_from_directory,
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from config import Config
from models import db, User, Assignment, Submission, Feedback


ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "gif"}


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    @app.context_processor
    def inject_now():
        return {"now": datetime.utcnow()}

    def allowed_file(filename):
        return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

    def login_required(role=None):
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                if "user_id" not in session:
                    flash("Please log in to continue.", "warning")
                    return redirect(url_for("login"))
                if role and session.get("role") != role:
                    flash("You do not have permission to access this page.", "danger")
                    return redirect(url_for("index"))
                return f(*args, **kwargs)
            return wrapper
        return decorator

    @app.route("/")
    def index():
        if "user_id" in session:
            if session.get("role") == "teacher":
                return redirect(url_for("teacher_dashboard"))
            else:
                return redirect(url_for("student_dashboard"))
        return redirect(url_for("login"))

    # Authentication
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            role = request.form.get("role")

            if not name or not email or not password or role not in {"teacher", "student"}:
                flash("All fields are required.", "danger")
                return render_template("register.html")

            existing = User.query.filter_by(email=email).first()
            if existing:
                flash("Email already registered. Please log in.", "warning")
                return redirect(url_for("login"))

            user = User(
                name=name,
                email=email,
                password_hash=generate_password_hash(password),
                role=role,
            )
            db.session.add(user)
            db.session.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))

        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            user = User.query.filter_by(email=email).first()
            if not user or not check_password_hash(user.password_hash, password):
                flash("Invalid email or password.", "danger")
                return render_template("login.html")

            session["user_id"] = user.id
            session["user_name"] = user.name
            session["role"] = user.role

            flash(f"Welcome back, {user.name}!", "success")
            if user.role == "teacher":
                return redirect(url_for("teacher_dashboard"))
            else:
                return redirect(url_for("student_dashboard"))

        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for("login"))

    # Teacher Views
    @app.route("/teacher/dashboard")
    @login_required(role="teacher")
    def teacher_dashboard():
        teacher_id = session["user_id"]
        assignments = Assignment.query.filter_by(teacher_id=teacher_id).order_by(Assignment.created_at.desc()).all()

        total_assignments = len(assignments)
        total_submissions = Submission.query.join(Assignment).filter(Assignment.teacher_id == teacher_id).count()
        graded_submissions = Submission.query.join(Assignment).filter(
            Assignment.teacher_id == teacher_id, Submission.status == "graded"
        ).count()
        pending_submissions = total_submissions - graded_submissions

        return render_template(
            "teacher_dashboard.html",
            assignments=assignments,
            total_assignments=total_assignments,
            total_submissions=total_submissions,
            graded_submissions=graded_submissions,
            pending_submissions=pending_submissions,
        )

    @app.route("/teacher/assignments/new", methods=["GET", "POST"])
    @login_required(role="teacher")
    def create_assignment():
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            due_date_str = request.form.get("due_date", "").strip()

            if not title or not description or not due_date_str:
                flash("All fields are required.", "danger")
                return render_template("create_assignment.html")

            try:
                due_date = datetime.strptime(due_date_str, "%Y-%m-%dT%H:%M")
            except ValueError:
                flash("Invalid due date format.", "danger")
                return render_template("create_assignment.html")

            assignment = Assignment(
                title=title,
                description=description,
                due_date=due_date,
                teacher_id=session["user_id"],
            )
            db.session.add(assignment)
            db.session.commit()
            flash("Assignment created successfully.", "success")
            return redirect(url_for("teacher_dashboard"))

        return render_template("create_assignment.html")

    @app.route("/teacher/assignments/<int:assignment_id>")
    @login_required(role="teacher")
    def view_assignment(assignment_id):
        assignment = Assignment.query.get_or_404(assignment_id)
        if assignment.teacher_id != session["user_id"]:
            flash("You do not have permission to view this assignment.", "danger")
            return redirect(url_for("teacher_dashboard"))

        submissions = Submission.query.filter_by(assignment_id=assignment.id).all()
        return render_template(
            "assignment_detail.html",
            assignment=assignment,
            submissions=submissions,
        )

    @app.route("/teacher/submissions/<int:submission_id>", methods=["GET", "POST"])
    @login_required(role="teacher")
    def review_submission(submission_id):
        submission = Submission.query.get_or_404(submission_id)
        if submission.assignment.teacher_id != session["user_id"]:
            flash("You do not have permission to review this submission.", "danger")
            return redirect(url_for("teacher_dashboard"))

        if request.method == "POST":
            try:
                score = float(request.form.get("score", "0"))
                max_score = float(request.form.get("max_score", "100"))
                rubric_clarity = int(request.form.get("rubric_clarity", "3"))
                rubric_completion = int(request.form.get("rubric_completion", "3"))
                rubric_presentation = int(request.form.get("rubric_presentation", "3"))
            except ValueError:
                flash("Please enter valid numeric values for scores and rubrics.", "danger")
                return render_template("review_submission.html", submission=submission)

            comments = request.form.get("comments", "").strip()

            if not (1 <= rubric_clarity <= 5 and 1 <= rubric_completion <= 5 and 1 <= rubric_presentation <= 5):
                flash("Rubric values must be between 1 and 5.", "danger")
                return render_template("review_submission.html", submission=submission)

            if submission.feedback:
                feedback = submission.feedback
                feedback.score = score
                feedback.max_score = max_score
                feedback.rubric_clarity = rubric_clarity
                feedback.rubric_completion = rubric_completion
                feedback.rubric_presentation = rubric_presentation
                feedback.comments = comments
            else:
                feedback = Feedback(
                    submission_id=submission.id,
                    teacher_id=session["user_id"],
                    score=score,
                    max_score=max_score,
                    rubric_clarity=rubric_clarity,
                    rubric_completion=rubric_completion,
                    rubric_presentation=rubric_presentation,
                    comments=comments,
                )
                db.session.add(feedback)

            submission.status = "graded"
            db.session.commit()
            flash("Feedback saved successfully.", "success")
            return redirect(url_for("view_assignment", assignment_id=submission.assignment_id))

        return render_template("review_submission.html", submission=submission)

    # Student Views
    @app.route("/student/dashboard")
    @login_required(role="student")
    def student_dashboard():
        student_id = session["user_id"]
        assignments = Assignment.query.order_by(Assignment.due_date.asc()).all()

        submissions = Submission.query.filter_by(student_id=student_id).all()
        submissions_by_assignment = {s.assignment_id: s for s in submissions}

        return render_template(
            "student_dashboard.html",
            assignments=assignments,
            submissions_by_assignment=submissions_by_assignment,
            now=datetime.utcnow(),
        )

    @app.route("/assignments/<int:assignment_id>/submit", methods=["GET", "POST"])
    @login_required(role="student")
    def submit_assignment(assignment_id):
        assignment = Assignment.query.get_or_404(assignment_id)
        student_id = session["user_id"]

        submission = Submission.query.filter_by(
            assignment_id=assignment_id,
            student_id=student_id
        ).first()

        if request.method == "POST":
            text_response = request.form.get("text_response", "").strip()
            file = request.files.get("file")

            file_path = submission.file_path if submission else None

            if file and file.filename:
                if allowed_file(file.filename):
                    filename = secure_filename(f"{student_id}_{assignment_id}_{file.filename}")
                    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    file.save(save_path)
                    file_path = filename
                else:
                    flash("File type not allowed.", "danger")
                    return render_template("submit_assignment.html", assignment=assignment, submission=submission)

            if submission:
                submission.text_response = text_response or submission.text_response
                submission.file_path = file_path
                submission.submitted_at = datetime.utcnow()
                submission.status = "submitted"
            else:
                submission = Submission(
                    assignment_id=assignment_id,
                    student_id=student_id,
                    text_response=text_response,
                    file_path=file_path,
                )
                db.session.add(submission)
                db.session.flush()  # make sure submission.id exists

            plagiarism_score = calculate_plagiarism_score(assignment_id, submission.id)
            submission.plagiarism_score = plagiarism_score

            db.session.commit()
            flash("Submission saved successfully.", "success")
            return redirect(url_for("student_dashboard"))

        return render_template("submit_assignment.html", assignment=assignment, submission=submission)

    def calculate_plagiarism_score(assignment_id, submission_id):
        current = Submission.query.get(submission_id)
        if not current or not current.text_response:
            return 0.0

        current_words = set(current.text_response.lower().split())
        if not current_words:
            return 0.0

        other_submissions = Submission.query.filter(
            Submission.assignment_id == assignment_id,
            Submission.id != submission_id
        ).all()

        max_similarity = 0.0
        for sub in other_submissions:
            if not sub.text_response:
                continue
            other_words = set(sub.text_response.lower().split())
            if not other_words:
                continue
            intersection = current_words.intersection(other_words)
            union = current_words.union(other_words)
            similarity = len(intersection) / len(union)
            if similarity > max_similarity:
                max_similarity = similarity

        return round(max_similarity * 100, 2)

    @app.route("/student/submissions")
    @login_required(role="student")
    def student_submissions():
        student_id = session["user_id"]
        submissions = Submission.query.filter_by(student_id=student_id).order_by(Submission.submitted_at.desc()).all()
        return render_template("student_submissions.html", submissions=submissions)

    @app.route("/student/analytics")
    @login_required(role="student")
    def student_analytics():
        student_id = session["user_id"]
        submissions = Submission.query.filter_by(student_id=student_id).all()

        data = []
        total_score = 0.0
        total_max = 0.0

        for sub in submissions:
            if sub.feedback:
                pct = (sub.feedback.score / sub.feedback.max_score) * 100 if sub.feedback.max_score else 0
                data.append({
                    "assignment_title": sub.assignment.title,
                    "score": sub.feedback.score,
                    "max_score": sub.feedback.max_score,
                    "percent": round(pct, 2),
                })
                total_score += sub.feedback.score
                total_max += sub.feedback.max_score

        overall_percent = round((total_score / total_max) * 100, 2) if total_max else 0.0

        return render_template(
            "student_analytics.html",
            data=data,
            overall_percent=overall_percent,
        )

    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    @app.errorhandler(413)
    def file_too_large(e):
        flash("File is too large. Maximum size is 16MB.", "danger")
        return redirect(request.referrer or url_for("index"))

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
