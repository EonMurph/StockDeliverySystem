import sqlite3  # imported just for `sqlite3.IntegrityError`
from flask import (Flask,
                   render_template,
                   url_for, redirect, request,
                   session, g)
from flask_session import Session
from database import get_db, close_db
from forms import (RegistrationForm, LogInForm, PermissionsForm,
                   ProductForm, StoreForm, DeliveriesForm)
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
    g.store = session.get("store_id", None)


def restricted(view, restriction):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if any([restriction == "admin" and g.admin is False,
                restriction == "manager" and g.manager is False]):
            session["restrictions"] = restriction
            session["restricted"] = True

            return redirect(url_for("homepage", next=request.url))
        return view(*args, **kwargs)
    return wrapped_view


# partial function found at https://stackoverflow.com/a/25827070
admin_required = partial(restricted, restriction="admin")
manager_required = partial(restricted, restriction="manager")


@app.route("/", methods=["GET", "POST"])
def homepage():
    if g.user:
        return render_template("homepage.html")

    else:
        return redirect("register")


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    db = get_db()
    query = "SELECT store_id from stores;"
    form.store_id.choices = [result["store_id"]
                             for result in db.execute(query).fetchall()]

    tips = list(glob("./templates/tips/*.html"))
    for i in range(len(tips)):
        parent = path.basename(path.dirname(tips[i]))
        file_name = path.basename(tips[i])
        tips[i] = str(path.join(parent, file_name)).replace("\\", "/")
    # TODO populate tips and remove next line
    index = choice(tips) if tips else "index.html"

    if form.validate_on_submit():
        user_id = form.user_id.data
        password = form.password.data
        password2 = form.password2.data
        store_id = form.store_id.data

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

            query = """
                    INSERT INTO employees (store_id, employee_id)
                    VALUES (?, ?);
                    """
            db.execute(query, (store_id, user_id))

            db.commit()

            session["user_id"] = user_id
            session["store_id"] = store_id

    return render_template(index, form=form)


@app.route("/log_in", methods=["GET", "POST"])
def log_in():
    form = LogInForm()

    if form.validate_on_submit():
        user_id = form.user_id.data
        password = form.password.data

        db = get_db()
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
                else:
                    query = """
                            SELECT store_id
                            FROM employees
                            WHERE employee_id = ?"""
                    store_id = db.execute(query, (user_id, )).fetchone()[
                        "store_id"]
                    session["store_id"] = store_id

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
    db = get_db()
    message = ''

    query = """
            SELECT *
            FROM users
            WHERE admin = 0
                AND manager = 0;
            """
    users = [result["user_id"]
             for result in db.execute(query).fetchall()]
    form.user_ids.choices = users

    query = """
            SELECT store_id
            FROM stores;
            """
    store_ids = [result["store_id"] for result in db.execute(query).fetchall()]
    form.store_id.choices = store_ids

    if form.validate_on_submit():
        user_id = form.user_ids.data
        store_id = form.store_id.data
        permission = "admin" if form.admin_submit.data else "manager"

        raise_permission(permission, user_id, db)

        if permission == "admin":
            query = """
                    DELETE FROM employees
                    WHERE employee_id = ?;
                    """
            db.execute(query, (user_id, ))
        else:
            if not store_id:
                form.store_id.errors.append(
                    "This input is required with a manager promotion.")
            else:
                manager_id_query = """
                        SELECT manager_id
                        FROM stores
                        WHERE store_id = ?;
                        """
                manager_id = db.execute(manager_id_query, (store_id, )).fetchone()[
                    "manager_id"]
                demote_query = """
                        UPDATE users
                        SET manager = 0
                        WHERE user_id = ?;
                        """
                db.execute(demote_query, (manager_id, ))

                query = """
                        UPDATE stores
                        SET manager_id = ?
                        WHERE store_id = ?;
                        """
                db.execute(query, (user_id, store_id))

        db.commit()
        message = f"User {user_id} was successfully made {permission}."

    return render_template("raise_permissions.html", form=form, message=message)


def raise_permission(permission, user_id, db):
    query = f"""
                UPDATE users
                SET {permission} = 1
                WHERE user_id = ?;
                """
    db.execute(query, (user_id, ))

# TODO route for removing managers


@app.route("/add_store", methods=["GET", "POST"])
@admin_required
def add_store():
    form = StoreForm()
    db = get_db()

    users_query = """
                SELECT user_id
                FROM users
                WHERE admin = 0;
                """
    users = [result["user_id"]
             for result in db.execute(users_query).fetchall()]
    form.manager_id.choices = users

    if form.validate_on_submit():
        manager_id = form.manager_id.data

        store_query = """
                    INSERT INTO stores (manager_id)
                    VALUES (?);
                    """
        raise_permission("manager", manager_id, db)
        db.execute(store_query, (manager_id, ))
        db.commit()

    return render_template("add_store.html", form=form)


@app.route("/add_product", methods=["GET", "POST"])
@admin_required
def add_product():
    form = ProductForm()

    if form.validate_on_submit():
        product_name = form.product_name.data
        product_image = form.product_image.data
        # TODO upload image to static folder

        db = get_db()
        query = """
                INSERT INTO products (product_name, product_image)
                VALUES (?, ?);
                """
        db.execute(query, (product_name, product_image))
        db.commit()

    return render_template("add_product.html", form=form)


# TODO route for soonest delivery
# TODO route for adding delivery days
@app.route("/add_delivery", methods=["GET", "POST"])
@admin_required
def add_deliveries():
    form = DeliveriesForm()

    db = get_db()
    query = """
            SELECT store_id
            FROM stores;
            """
    choices = [result["store_id"] for result in db.execute(query).fetchall()]
    form.to_store.choices = choices
    form.from_store.choices = choices

    if form.validate_on_submit():
        to_store = form.to_store.data
        from_store = form.from_store.data
        day = form.day.data

        query = """
                INSERT INTO store_delivery_schedule
                VALUES (?, ?, ?);
                """
        db.execute(query, (to_store, from_store, day))
        db.commit()

    return render_template("add_delivery.html", form=form)


# TODO showing stock for their specific store
# TODO show amount of stock
@app.route("/stock")
def view_stock():
    db = get_db()
    query = """
            SELECT *
            FROM products;
            """
    products = db.execute(query).fetchall()

    return render_template("products_page.html", products=products)


# TODO route for "scanning" and "buying" stock
# TODO route for notifications when stock is low
# have it on the homepage
# a quick welcome back, these products are low in stock, and then a button for which ones you'd like to order
