from flask import (Flask,
                   render_template,
                   session,
                   url_for, redirect,
                   g,
                   request)
from flask_session import Session
from database import get_db, close_db
from forms import RegistrationForm, LogInForm
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.config["SECRET_KEY"] = "this-is-my-secret-key"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.teardown_appcontext(close_db)


@app.before_request
def load_logged_in_user():
    g.user = session.get("user_id", None)


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("login", next=request.url))
        return view(*args, **kwargs)
    return wrapped_view


@app.route("/")
def homepage():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm(request.form)

    if form.validate_on_submit():
        user_id = form.user_id.data
        password = form.password.data
        password2 = form.password2.data
        

        db = get_db()
        query = """
                SELECT *
                FROM users
                WHERE user_id = ?;
                """
        if db.execute(query, (user_id,)).fetchone():
            form.user_id.errors.append("Username already taken.")
        else:
            query = """
                    INSERT INTO users (user_id, password)
                    VALUES (?, ?)
                    """
            db.execute(query, (user_id, generate_password_hash(password)))
            db.commit()

            session["user_id"] = user_id
            return redirect(url_for("homepage"))

    return render_template("register.html", form=form, title="Registration")


@app.route("/log_in", methods=["GET", "POST"])
def log_in():
    form = LogInForm()
    db = get_db()
    incorrect_error = ""

    if form.validate_on_submit():
        user_id = form.user_id.data
        password = form.password.data

        query = """
                SELECT user_id, password
                FROM users
                WHERE user_id = ?;
                """
        if user_data := db.execute(query, (user_id,)).fetchone():
            if check_password_hash(user_data["password"], password):
                session["user_id"] = user_id
                next_page = request.args.get("next") or url_for("homepage")

                return redirect(next_page)

        else:
            incorrect_error = "Incorrect username or password."

    return render_template("log_in.html", form=form, title="Log In", incorrect_error=incorrect_error)


@app.route("/log_out")
def log_out():
    session.clear()

    return redirect(url_for("homepage"))
