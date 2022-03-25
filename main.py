from forms import RegisterUserForm, LoginUserForm, ToDoForm
from flask import Flask, abort, redirect, render_template, request, url_for
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
import sqlalchemy.exc
from sqlalchemy.orm import relationship
from urllib.parse import urlparse, urljoin
import werkzeug
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

#App Inits
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("flask_key")
ckeditor = CKEditor(app)
Bootstrap(app)
login_manager = LoginManager()
login_manager.init_app(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///to-do.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#User and Task Tables
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), unique=True, nullable=False)
    username = db.Column(db.String(250), unique=True, nullable=False)
    complete = db.Column(db.Integer)
    tasks = relationship("ToDo", back_populates="author")

class ToDo(db.Model):
    __tablename__ = "ToDos"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    description = db.Column(db.Text, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="tasks")

db.create_all()

##Creates the is_safe_url function for use in login
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_year():
    year = datetime.now().year
    return dict(year=year)

##Home, Login, Register, and Logout Routes##
@app.route("/")
def home():
    return render_template("index.html")

@app.route('/register', methods=["GET", "POST"])
def register():
    error = ""
    form = RegisterUserForm()
    if form.validate_on_submit():
        try:
            new_user = User(
                username=form.username.data,
                email=form.email.data,
                password=werkzeug.security.generate_password_hash(password=form.password.data, method="pbkdf2:sha256", salt_length=8),
                complete=0
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("user_home", user_id=new_user.id))
        except sqlalchemy.exc.IntegrityError:
            error = "You've already signed up using that email. Please use the login function instead."
    return render_template("register.html", form=form, error=error)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginUserForm()
    error = ""
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            password=form.password.data
        )
        check_user = User.query.filter_by(email=user.email).first()
        if not check_user or user.email != check_user.email:
            error = "Sorry, that email does not match our records. Please try again."
        elif not werkzeug.security.check_password_hash(check_user.password, user.password):
            error = "Sorry, that password does not match our records. Please try again."
        elif user.email == check_user.email and werkzeug.security.check_password_hash(check_user.password,
                                                                                      user.password):
            user = check_user
            login_user(user)
            next = request.args.get("next")
            if not is_safe_url(next):
                return abort(404)
            else:
                return redirect(url_for("user_home", user_id=user.id))
    return render_template("login.html", form=form, error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

##User Routes##
@app.route("/home/<int:user_id>", methods=["GET", "POST"])
def user_home(user_id):
    user = User.query.get(user_id)
    if current_user.is_authenticated:
        todos = ToDo.query.filter_by(user_id=current_user.id).all()
        try:
            message = f"You currently have {len(todos)} To-Dos!"
        except TypeError:
            message = f"You currently have no To-Dos!"
        form = ToDoForm()
        if request.method == "POST":
            new_task = ToDo(
                name=form.name.data,
                description=form.description.data,
                start_date=form.start_date.data,
                end_date=form.end_date.data,
                user_id=current_user.id
            )
            db.session.add(new_task)
            db.session.commit()
            return redirect(url_for("user_home", user_id=current_user.id))
        return render_template("user-home.html", user=user, form=form, message=message, todos=todos)

@app.route("/check-off/<int:task_id>")
def check_off(task_id):
    task_to_check_off = ToDo.query.get(task_id)
    user = User.query.get(current_user.id)
    if current_user.is_authenticated:
        db.session.delete(task_to_check_off)
        user.complete += 1
        db.session.commit()
        return redirect(url_for("user_home", user_id=current_user.id))

@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit(task_id):
    if current_user.is_authenticated:
        user = User.query.get(current_user.id)
        task_edit = ToDo.query.get(task_id)
        todos = ToDo.query.filter_by(user_id=current_user.id).all()
        try:
            message = f"You currently have {len(todos)} To-Dos!"
        except TypeError:
            message = f"You currently have no To-Dos!"
        edit_form = ToDoForm(
            name=task_edit.name,
            description=task_edit.description,
            start_date=task_edit.start_date,
            end_date=task_edit.end_date,
        )
        if request.method == "POST":
            task_edit.name = edit_form.name.data
            task_edit.description = edit_form.description.data
            task_edit.start_date = edit_form.start_date.data
            task_edit.end_date = edit_form.end_date.data
            db.session.commit()
            return redirect(url_for("user_home", user_id=current_user.id))
        return render_template("edit.html", user_id=current_user.id, form=edit_form, user=user, message=message)

@app.route("/delete/<int:task_id>")
def delete_task(task_id):
    task_to_delete = ToDo.query.get(task_id)
    if current_user.is_authenticated:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect(url_for("user_home", user_id=current_user.id))


if __name__ == "__main__":
    app.run(debug=True)