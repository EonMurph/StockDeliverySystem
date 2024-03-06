import sqlite3  # imported just for `sqlite3.IntegrityError`
from flask import (Flask,
                   render_template,
                   url_for, redirect, request,
                   session, g)
from flask_session import Session
from database import get_db, close_db
from forms import (RegistrationForm, LogInForm, PermissionsForm)
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps, partial
from random import choice
from os import path
from glob import glob

app = Flask(__name__)
app.config["SECRET_KEY"] = "this-is-my-secret-key"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.teardown_appcontext(close_db)


@app.before_request
def init_admin():
    # TODO see if you can get `before_first_request` working
    """ # next line found on https://stackoverflow.com/questions/73570041/flask-deprecated-before-first-request-how-to-update
    app.before_request_funcs[None].remove(init_admin) """

    db = get_db()
    query = """
            INSERT INTO users (user_id, password, admin)
            VALUES (1, ?, 1);
            """
    try:
        db.execute(query, (generate_password_hash("secret"), ))
        db.commit()
    except sqlite3.IntegrityError:
        pass


@app.before_request
def load_logged_in_user():
    g.user = session.get("user_id", None)
    g.admin = session.get("admin", False)
    g.manager = session.get("manager", False)
    g.restrictions = session.get("restrictions", None)
    g.restricted = session.get("restricted", False)


def restricted(view, restriction):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if any([restriction == "admin" and g.admin is False,
                restriction == "manager" and g.manager is False]):
            session["restrictions"] = restriction
            session["restricted"] = True

            return redirect(url_for("log_in", next=request.url))
        return view(*args, **kwargs)
    return wrapped_view


# partial function found at https://stackoverflow.com/a/25827070
admin_required = partial(restricted, restriction="admin")
manager_required = partial(restricted, restriction="manager")


@app.route("/")
def homepage():
    if g.user:
        return render_template("homepage.html")
    tips = list(glob("./templates/tips/*.html"))
    for i in range(len(tips)):
        parent = path.basename(path.dirname(tips[i]))
        file_name = path.basename(tips[i])
        tips[i] = str(path.join(parent, file_name)).replace("\\", "/")

    # TODO populate tips and remove next line
    index = choice(tips) if tips else "index.html"

    return render_template(index)


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

    return render_template("register.html", form=form)


@app.route("/log_in", methods=["GET", "POST"])
def log_in():
    form = LogInForm()
    db = get_db()

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

                session.clear()

                query = """
                        SELECT *
                        FROM users
                        WHERE user_id = ?;
                        """
                user_data = db.execute(query, (user_id,)).fetchone()

                if user_data["admin"] == 1:
                    session["admin"] = True

                session["user_id"] = user_id
                next_page = request.args.get("next") or url_for("homepage")

                return redirect(next_page)

            else:
                form.password.errors.append("Incorrect password.")

        else:
            form.user_id.errors.append("Incorrect user id.")

    return render_template("log_in.html", form=form)


@app.route("/log_out")
def log_out():
    session.clear()

    return redirect(url_for("homepage"))


@app.route("/raise_permissions", methods=["GET", "POST"])
@admin_required
def raise_permissions():
    form = PermissionsForm()
    message = ''

    query = """
            SELECT *
            FROM users
            WHERE admin = 0
                AND manager = 0;
            """

    db = get_db()
    users = [result["user_id"]
             for result in db.execute(query).fetchall()]

    form.user_ids.choices = users

    if form.validate_on_submit():
        user_id = form.user_ids.data
        permission = "admin" if form.admin_submit.data else "manager"

        print(user_id, permission)

        query = f"""
                UPDATE users
                SET {permission} = 1
                WHERE user_id = ?;
                """
        db.execute(query, (user_id, ))
        db.commit()
        message = f"User {user_id} was successfully made {permission}."

    return render_template("raise_permissions.html", form=form, message=message)
