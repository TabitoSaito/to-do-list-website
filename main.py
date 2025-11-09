from flask import Flask, render_template, redirect, url_for, flash
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Text, and_
import random
from flask_bootstrap import Bootstrap5
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
import datetime
from forms import RegisterForm, LoginForm, AddListForm, AddTaskForm
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
Bootstrap5(app)


class Base(DeclarativeBase):
    pass


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///to-do-lists.db"
db = SQLAlchemy(model_class=Base)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)


class ToDoList(db.Model):
    __tablename__ = "to_do_list"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="lists")
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    created_on: Mapped[str] = mapped_column(String(250), nullable=False)
    tasks = relationship("Task", back_populates="parent_list")


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    lists = relationship("ToDoList", back_populates="author")


class Task(db.Model):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(255), nullable=False)
    list_id: Mapped[str] = mapped_column(Integer, db.ForeignKey("to_do_list.id"))
    parent_list = relationship("ToDoList", back_populates="tasks")


with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


@app.route("/")
def home():
    if current_user.is_authenticated:
        result = db.session.execute(
            db.select(ToDoList).where(ToDoList.author == current_user)
        )
        to_do_lists = result.scalars().all()
    else:
        to_do_lists = []
    return render_template("index.html", to_do_lists=to_do_lists)


@app.route("/random")
def random_list():
    result = db.session.execute(db.select(ToDoList))
    result_list = result.scalars().all()
    if len(result_list) == 0:
        return redirect(url_for("home"))
    else:
        random_id = random.choice(result_list).id
        return redirect(url_for("to_do_list", list_id=random_id))


@app.route("/list/<list_id>")
def to_do_list(list_id):
    todo_list = db.get_or_404(ToDoList, list_id)
    result1 = db.session.execute(
        db.select(Task).where(and_(Task.list_id == list_id, Task.status == "TODO"))
    )
    tasks_todo = result1.scalars().all()

    result2 = db.session.execute(
        db.select(Task).where(
            and_(Task.list_id == list_id, Task.status == "IN PROGRESS")
        )
    )
    tasks_in_progress = result2.scalars().all()

    result3 = db.session.execute(
        db.select(Task).where(and_(Task.list_id == list_id, Task.status == "COMPLETED"))
    )
    tasks_completed = result3.scalars().all()

    return render_template(
        "to-do-list.html",
        todo_list=todo_list,
        list_id=list_id,
        tasks_todo=tasks_todo,
        tasks_in_progress=tasks_in_progress,
        tasks_completed=tasks_completed,
    )


@app.route("/add-list", methods=["GET", "POST"])
def add_list():
    form = AddListForm()
    if form.validate_on_submit():
        result = db.session.execute(
            db.select(ToDoList).where(ToDoList.title == form.title.data)
        )
        to_do = result.scalar()
        if to_do:
            flash("A To-Do-List with that name already exists.")
            return redirect(url_for("add_list.html"))

        new_list = ToDoList(
            title=form.title.data,
            created_on=datetime.date.today().strftime("%B %d, %Y"),
            author=current_user,
        )
        db.session.add(new_list)
        db.session.commit()

        return redirect(url_for("home"))
    return render_template("add_list.html", form=form, current_user=current_user)


@app.route("/add-task/<list_id>", methods=["GET", "POST"])
def add_task(list_id):
    form = AddTaskForm()
    if form.validate_on_submit():
        new_task = Task(
            title=form.title.data,
            text=form.description.data,
            status="TODO",
            list_id=list_id,
        )
        db.session.add(new_task)
        db.session.commit()

        return redirect(url_for("to_do_list", list_id=list_id))
    return render_template("add_task.html", form=form, current_user=current_user)


@app.route("/switch-to-TODO/<task_id>")
def switch_to_todo(task_id):
    task_to_switch = db.get_or_404(Task, task_id)
    task_to_switch.status = "TODO"
    db.session.commit()
    to_do_list_from_task = db.get_or_404(ToDoList, task_to_switch.parent_list.id)
    return redirect(url_for("to_do_list", list_id=to_do_list_from_task.id))


@app.route("/switch-to-IN_PROGRESS/<task_id>")
def switch_to_progress(task_id):
    task_to_switch = db.get_or_404(Task, task_id)
    task_to_switch.status = "IN PROGRESS"
    db.session.commit()
    to_do_list_from_task = db.get_or_404(ToDoList, task_to_switch.parent_list.id)
    return redirect(url_for("to_do_list", list_id=to_do_list_from_task.id))


@app.route("/switch-to-COMPLETED/<task_id>")
def switch_to_completed(task_id):
    task_to_switch = db.get_or_404(Task, task_id)
    task_to_switch.status = "COMPLETED"
    db.session.commit()
    to_do_list_from_task = db.get_or_404(ToDoList, task_to_switch.parent_list.id)
    return redirect(url_for("to_do_list", list_id=to_do_list_from_task.id))


@app.route("/delete_task/<task_id>")
def delete_task(task_id):
    task_to_delete = db.get_or_404(Task, task_id)
    to_do_list_from_task = db.get_or_404(ToDoList, task_to_delete.parent_list.id)
    db.session.delete(task_to_delete)
    db.session.commit()
    return redirect(url_for("to_do_list", list_id=to_do_list_from_task.id))


@app.route("/delete_list/<list_id>")
def delete_list(list_id):
    list_to_delete = db.get_or_404(ToDoList, list_id)
    db.session.execute(db.delete(Task).where(Task.parent_list == list_to_delete))
    db.session.delete(list_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        result = db.session.execute(
            db.select(User).where(User.email == form.email.data)
        )
        user = result.scalar()
        if user:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for("login"))

        hash_and_salted_password = generate_password_hash(
            form.password.data, method="pbkdf2:sha256", salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for("home"))
    return render_template("register.html", form=form, current_user=current_user)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        result = db.session.execute(
            db.select(User).where(User.email == form.email.data)
        )
        user = result.scalar()
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for("login"))
        elif not check_password_hash(user.password, password):
            flash("Password incorrect, please try again.")
            return redirect(url_for("login"))
        else:
            login_user(user)
            return redirect(url_for("home"))

    return render_template("login.html", form=form, current_user=current_user)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


def main() -> None:
    app.run(debug=True)


if __name__ == "__main__":
    main()
