"""
admin login - username: 1, password: secret
all manager logins are 111111 for store 1, 222222 for store 2, etc. and all passwords are 123
"""

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
from delivery_setup import get_delivery_dict, get_delivery_table, DAYS_OF_WEEK, get_source_stores
from search_funcs import perform_search, get_duration, get_route
from datetime import date

app = Flask(__name__)
app.config["SECRET_KEY"] = "this-is-my-secret-key"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.teardown_appcontext(close_db)


@app.before_request
def init_admin():
    db = get_db()
    admin_query = """
            INSERT INTO users (user_id, password, admin)
            VALUES (1, ?, 1);
            """
    try:
        db.execute(admin_query, (generate_password_hash("secret"), ))
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

            return redirect(url_for("log_in", next=request.url))
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
    store_id_query = "SELECT store_id FROM stores;"
    form.store_id.choices = [result["store_id"]
                             for result in db.execute(store_id_query).fetchall()]

    # tips = list(glob("./templates/tips/*.html"))
    # for i in range(len(tips)):
    #     parent = path.basename(path.dirname(tips[i]))
    #     file_name = path.basename(tips[i])
    #     tips[i] = str(path.join(parent, file_name)).replace("\\", "/")
    # index = choice(tips) if tips else "index.html"

    if form.validate_on_submit():
        user_id = form.user_id.data
        password = form.password.data
        password2 = form.password2.data
        store_id = form.store_id.data

        db = get_db()
        conflict_query = """
                SELECT *
                FROM users
                WHERE user_id = ?;
                """
        if db.execute(conflict_query, (user_id,)).fetchone():
            form.user_id.errors.append("Username already taken.")
        else:
            create_user_query = """
                    INSERT INTO users (user_id, password)
                    VALUES (?, ?)
                    """
            db.execute(create_user_query,
                       (user_id, generate_password_hash(password)))

            create_employee_query = """
                    INSERT INTO employees (store_id, employee_id)
                    VALUES (?, ?);
                    """
            db.execute(create_employee_query, (store_id, user_id))

            db.commit()

            session["user_id"] = user_id
            session["store_id"] = store_id

            return redirect(url_for("homepage"))

    return render_template("index.html", form=form)


@app.route("/log_in", methods=["GET", "POST"])
def log_in():
    form = LogInForm()

    if form.validate_on_submit():
        user_id = form.user_id.data
        password = form.password.data

        db = get_db()
        find_user_query = """
                SELECT *
                FROM users
                WHERE user_id = ?;
                """
        if user_data := db.execute(find_user_query, (user_id,)).fetchone():
            if check_password_hash(user_data["password"], password):

                session.clear()

                if user_data["admin"] == 1:
                    session["admin"] = True
                else:
                    if user_data["manager"] == 1:
                        session["manager"] = True

                    find_store_query = """
                            SELECT store_id
                            FROM employees
                            WHERE employee_id = ?"""
                    store_id = db.execute(find_store_query, (user_id, )).fetchone()[
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

    valid_users_query = """
            SELECT *
            FROM users
            WHERE admin = 0
                AND manager = 0;
            """
    users = [result["user_id"]
             for result in db.execute(valid_users_query).fetchall()]
    form.user_ids.choices = users

    store_ids_query = """
            SELECT store_id
            FROM stores;
            """
    store_ids = [result["store_id"]
                 for result in db.execute(store_ids_query).fetchall()]
    form.store_id.choices = store_ids

    if form.validate_on_submit():
        user_id = form.user_ids.data
        store_id = form.store_id.data
        permission = "admin" if form.admin_submit.data else "manager"

        raise_permission(permission, user_id, db)

        if permission == "admin":
            delete_employee_query = """
                    DELETE FROM employees
                    WHERE employee_id = ?;
                    """
            db.execute(delete_employee_query, (user_id, ))
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

                change_manager_query = """
                        UPDATE stores
                        SET manager_id = ?
                        WHERE store_id = ?;
                        """
                db.execute(change_manager_query, (user_id, store_id))

        db.commit()
        message = f"User {user_id} was successfully made {permission}."

    return render_template("raise_permissions.html", form=form, message=message)


def raise_permission(permission, user_id, db):
    raise_permissions_query = f"""
                UPDATE users
                SET {permission} = 1
                WHERE user_id = ?;
                """
    db.execute(raise_permissions_query, (user_id, ))


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

        db = get_db()
        create_product_query = """
                INSERT INTO products (product_name)
                VALUES (?);
                """
        db.execute(create_product_query, (product_name))
        db.commit()

    return render_template("add_product.html", form=form)


@app.route("/get_delivery/<int:product_id>", defaults={"order_day": DAYS_OF_WEEK.index(date.today().strftime("%a"))})
@app.route("/get_delivery/<int:product_id>/<int:order_day>")
def get_delivery(product_id, order_day):
    """Using an employee from store 3 with a product id of 3, will return a route when using the test data."""
    if g.store:
        db = get_db()
        delivery_table = get_delivery_table(db)
        delivery_dict = get_delivery_dict(delivery_table)
        source_stores = get_source_stores(db, product_id)

        target_store = int(g.store)
        delivery_timetable = perform_search(
            delivery_dict, target_store, source_stores, order_day)
        print(delivery_timetable)
        duration = get_duration(order_day, target_store, delivery_timetable)
        route = get_route(target_store, delivery_timetable)

        return render_template("fastest_delivery.html", route=route, duration=duration, product_id=product_id, target_store=target_store)
    return redirect(url_for("log_in"))


@app.route("/order_products/<int:product_id>")
def order_products(product_id):
    if not g.user:
        return redirect("register")
    if "cart" not in session:
        session["cart"] = {}
    if product_id not in session["cart"]:
        session["cart"][product_id] = 1
    else:
        session["cart"][product_id] += 1

    return redirect(url_for("cart"))


@app.route("/cart")
def cart():
    if not g.user:
        return redirect("register")
    if "cart" not in session:
        session["cart"] = {}
    names = {}
    db = get_db()
    for product_id in session["cart"]:
        product = db.execute("SELECT * FROM products WHERE product_id = ?;",
                             (product_id, )).fetchone()
        name = product["product_name"]
        names[product_id] = name

    return render_template("cart.html", cart=session["cart"], names=names)


@app.route("/add_delivery", methods=["GET", "POST"])
@admin_required
def add_deliveries():
    form = DeliveriesForm()

    db = get_db()
    store_ids_query = """
            SELECT store_id
            FROM stores;
            """
    choices = [result["store_id"]
               for result in db.execute(store_ids_query).fetchall()]
    form.to_store.choices = choices
    form.from_store.choices = choices

    if form.validate_on_submit():
        to_store = form.to_store.data
        from_store = form.from_store.data
        day = form.day.data

        create_route_query = """
                INSERT INTO store_delivery_schedule
                VALUES (?, ?, ?);
                """
        db.execute(create_route_query, (to_store, from_store, day))
        db.commit()

    return render_template("add_delivery.html", form=form)


@app.route("/view_stock")
def view_stock():
    db = get_db()
    all_stock_query = """
            SELECT *
            FROM products;
            """
    all_products = db.execute(all_stock_query).fetchall()
    products = []
    if g.store:
        store_specific_query = """
                SELECT DISTINCT *
                FROM products as p 
                    JOIN products_in_stores as pis
                        ON p.product_id = pis.product_id
                WHERE pis.store_id = ?;
                """
        products = db.execute(store_specific_query, (g.store, )).fetchall()
    
    return render_template("products_page.html", products=products, all_products=all_products)

@app.route("/admin_links")
def admin_links():
    return render_template("admin_links.html")