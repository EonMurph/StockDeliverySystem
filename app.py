from flask import Flask, render_template
from database import get_db, close_db
from forms import RegistrationForm
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = "this-is-my-secret-key"
app.teardown_appcontext(close_db)


@app.route("/")
def homepage():
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

    return render_template("register.html", form=form, title="Registration")
