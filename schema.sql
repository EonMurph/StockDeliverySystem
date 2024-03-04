DROP TABLE IF EXISTS users;

CREATE TABLE users
(
    user_id INTEGER PRIMARY KEY,
    password TEXT NOT NULL,
    admin BOOL NOT NULL DEFAULT '0',
    manager BOOL NOT NULL DEFAULT '0'
);
