PRAGMA foreign_keys = 1;

-- DROP TABLE IF EXISTS users;
-- DROP TABLE IF EXISTS products;
-- DROP TABLE IF EXISTS stores;
-- DROP TABLE IF EXISTS products_in_stores;
-- DROP TABLE IF EXISTS employees;

CREATE TABLE IF NOT EXISTS users
(
    user_id INTEGER PRIMARY KEY,
    password TEXT NOT NULL,
    admin BOOL NOT NULL DEFAULT '0',
    manager BOOL NOT NULL DEFAULT '0'
);

CREATE TABLE IF NOT EXISTS products
(
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    product_image TEXT NOT NULL DEFAULT 'default.png'
    
);

CREATE TABLE IF NOT EXISTS stores
(
    store_id INTEGER PRIMARY KEY AUTOINCREMENT,
    manager_id INTEGER NOT NULL,
    FOREIGN KEY (manager_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS product_in_stores
(
    product_id INTERGER NOT NULL,
    order_point INTEGER DEFAULT 10,
    store_id INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
    FOREIGN KEY (store_id) REFERENCES stores(store_id)
);

CREATE TABLE IF NOT EXISTS employees
(
    store_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
    FOREIGN KEY (employee_id) REFERENCES users(user_id)
);