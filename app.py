from flask import Flask, render_template, session, url_for, redirect
from flask_session import Session
from database import get_db, close_db
from forms import RegistrationForm, LogInForm
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = "this-is-my-secret-key"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.teardown_appcontext(close_db)


@app.route("/")
def homepage():
    if "user_id" not in session:
        session["user_id"] = None
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    db = get_db()

    if form.validate_on_submit():
        user_id = form.user_id.data
        password = form.password.data
        password2 = form.password2.data

        query = """
                SELECT *
                FROM users
                WHERE user_id = ?;
                """
        conflict_user = db.execute(query, (user_id, )).fetchone()
        if conflict_user:
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
        user_data = db.execute(query, (user_id, )).fetchone()
        if user_data:
            if check_password_hash(user_data["password"], password):
                session["user_id"] = user_id
                return redirect( url_for("homepage") )
            
        else:
            incorrect_error = "Incorrect username or password."
    return render_template("log_in.html", form=form, title="Log In", incorrect_error=incorrect_error)


@app.route("/log_out")
def log_out():
    session["user_id"] = None

    return redirect(url_for("homepage"))
