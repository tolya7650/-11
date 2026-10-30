"""SQLite data layer used by the demonstration PySide6 application.

The table structure follows the source files supplied for topic 3.  PostgreSQL DDL
is placed in sql/mir_velosipedov_postgresql.sql for work in pgAdmin.
"""
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_DIR / "data" / "mir_velosipedov.db"
SOURCE_DIR = PROJECT_DIR / "resources" / "source_data"


def get_connection() -> sqlite3.Connection:
    """Return a database connection with foreign keys enabled."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def create_schema(connection: sqlite3.Connection) -> None:
    """Create a normalized schema for the bicycle shop."""
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS subcategories (
            subcategory_id INTEGER PRIMARY KEY,
            category_id INTEGER NOT NULL REFERENCES categories(category_id),
            name TEXT NOT NULL,
            UNIQUE(category_id, name)
        );
        CREATE TABLE IF NOT EXISTS manufacturers (
            manufacturer_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS variants (
            variant_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY,
            category_id INTEGER NOT NULL REFERENCES categories(category_id),
            subcategory_id INTEGER NOT NULL REFERENCES subcategories(subcategory_id),
            manufacturer_id INTEGER NOT NULL REFERENCES manufacturers(manufacturer_id),
            image_name TEXT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            composition TEXT NOT NULL,
            base_price NUMERIC NOT NULL CHECK(base_price > 0),
            UNIQUE(name, manufacturer_id)
        );
        CREATE TABLE IF NOT EXISTS stock_items (
            stock_item_id INTEGER PRIMARY KEY,
            product_id INTEGER NOT NULL REFERENCES products(product_id),
            variant_id INTEGER NOT NULL REFERENCES variants(variant_id),
            quantity INTEGER NOT NULL CHECK(quantity >= 0),
            price NUMERIC NOT NULL CHECK(price > 0),
            UNIQUE(product_id, variant_id)
        );
        CREATE TABLE IF NOT EXISTS roles (
            role_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            last_name TEXT NOT NULL,
            first_name TEXT NOT NULL,
            patronymic TEXT,
            login TEXT NOT NULL UNIQUE,
            role_id INTEGER NOT NULL REFERENCES roles(role_id)
        );
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY,
            order_date TEXT NOT NULL,
            user_id INTEGER NOT NULL REFERENCES users(user_id)
        );
        CREATE TABLE IF NOT EXISTS order_items (
            order_item_id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL REFERENCES orders(order_id),
            stock_item_id INTEGER NOT NULL REFERENCES stock_items(stock_item_id),
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            unit_price NUMERIC NOT NULL CHECK(unit_price > 0)
        );
        """
    )


def _read_csv(filename: str) -> list[dict[str, str]]:
    with (SOURCE_DIR / filename).open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def initialise_database() -> None:
    """Create an empty database and import the supplied topic-3 CSV resources."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as connection:
        create_schema(connection)
        if connection.execute("SELECT COUNT(*) FROM products").fetchone()[0]:
            return
        product_rows = _read_csv("Products_import.csv")
        variant_rows = _read_csv("Variants_import.csv")
        stock_rows = _read_csv("Stock_Items_import.csv")
        user_rows = _read_csv("Users_import.csv")
        order_rows = _read_csv("Orders_import.csv")

        connection.executemany(
            "INSERT INTO roles(name) VALUES (?)",
            [("Администратор",), ("Менеджер",), ("Авторизованный пользователь",)],
        )
        for row in product_rows:
            connection.execute("INSERT OR IGNORE INTO categories(name) VALUES (?)", (row["Категория"],))
            category_id = connection.execute(
                "SELECT category_id FROM categories WHERE name = ?", (row["Категория"],)
            ).fetchone()[0]
            connection.execute(
                "INSERT OR IGNORE INTO subcategories(category_id, name) VALUES (?, ?)",
                (category_id, row["Подкатегория"]),
            )
            connection.execute("INSERT OR IGNORE INTO manufacturers(name) VALUES (?)", (row["Производство"],))
        for row in variant_rows:
            connection.execute("INSERT OR IGNORE INTO variants(name) VALUES (?)", (row["Вариант исполнения"],))
        for row in product_rows:
            category_id = connection.execute("SELECT category_id FROM categories WHERE name=?", (row["Категория"],)).fetchone()[0]
            subcategory_id = connection.execute(
                "SELECT subcategory_id FROM subcategories WHERE category_id=? AND name=?",
                (category_id, row["Подкатегория"]),
            ).fetchone()[0]
            manufacturer_id = connection.execute("SELECT manufacturer_id FROM manufacturers WHERE name=?", (row["Производство"],)).fetchone()[0]
            connection.execute(
                """INSERT INTO products(category_id,subcategory_id,manufacturer_id,image_name,name,description,composition,base_price)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (category_id, subcategory_id, manufacturer_id, row["Изображение"], row["Наименование товара"],
                 row["Описание"], row["Состав"], float(row["Цена"])),
            )
        for row in stock_rows:
            product_id = connection.execute(
                """SELECT p.product_id FROM products p JOIN manufacturers m ON m.manufacturer_id=p.manufacturer_id
                   WHERE p.name=? AND m.name=?""", (row["Наименование товара"], row["Производство"])
            ).fetchone()[0]
            variant_id = connection.execute("SELECT variant_id FROM variants WHERE name=?", (row["Вариант исполнения"],)).fetchone()[0]
            connection.execute(
                "INSERT INTO stock_items(product_id,variant_id,quantity,price) VALUES (?, ?, ?, ?)",
                (product_id, variant_id, int(row["Количество доступное для заказа"]), float(row["Цена варианта"])),
            )
        for row in user_rows:
            role_id = connection.execute("SELECT role_id FROM roles WHERE name=?", (row["Роль"],)).fetchone()[0]
            connection.execute(
                "INSERT INTO users(last_name,first_name,patronymic,login,role_id) VALUES (?, ?, ?, ?, ?)",
                (row["Фамилия"], row["Имя"], row["Отчество"], row["Логин"], role_id),
            )
        imported_orders: dict[int, int] = {}
        for row in order_rows:
            number = int(row["Номер заказа"])
            if number not in imported_orders:
                fio = row["ФИО"].split()
                user = connection.execute(
                    "SELECT user_id FROM users WHERE last_name=? AND first_name=? AND patronymic=?", tuple(fio)
                ).fetchone()
                if user:
                    connection.execute("INSERT INTO orders(order_id,order_date,user_id) VALUES (?, ?, ?)", (number, row["Дата заказа"], user[0]))
                    imported_orders[number] = number
            if number in imported_orders:
                stock = connection.execute(
                    """SELECT si.stock_item_id FROM stock_items si JOIN products p ON p.product_id=si.product_id
                    JOIN manufacturers m ON m.manufacturer_id=p.manufacturer_id JOIN variants v ON v.variant_id=si.variant_id
                    WHERE p.name=? AND m.name=? AND v.name=?""",
                    (row["Наименование товара"], row["Производство"], row["Вариант исполнения"]),
                ).fetchone()
                if stock:
                    connection.execute(
                        "INSERT INTO order_items(order_id,stock_item_id,quantity,unit_price) VALUES (?, ?, ?, ?)",
                        (number, stock[0], int(row["Количество"]), float(row["Цена за единицу"])),
                    )


def fetch_catalog(category: str = "Все категории", search: str = "") -> list[sqlite3.Row]:
    """Return products with minimum price and total available quantity."""
    query = """
        SELECT p.product_id, p.name, p.image_name, p.description, p.composition, p.base_price,
               c.name AS category, sc.name AS subcategory, m.name AS manufacturer,
               MIN(si.price) AS minimum_price, COALESCE(SUM(si.quantity), 0) AS quantity
        FROM products p
        JOIN categories c ON c.category_id=p.category_id
        JOIN subcategories sc ON sc.subcategory_id=p.subcategory_id
        JOIN manufacturers m ON m.manufacturer_id=p.manufacturer_id
        LEFT JOIN stock_items si ON si.product_id=p.product_id
        WHERE (:category='Все категории' OR c.name=:category)
          AND (p.name LIKE :term OR m.name LIKE :term OR c.name LIKE :term)
        GROUP BY p.product_id
        ORDER BY c.name, p.name
    """
    with get_connection() as connection:
        return connection.execute(query, {"category": category, "term": f"%{search.strip()}%"}).fetchall()


def fetch_categories() -> list[str]:
    with get_connection() as connection:
        return [row[0] for row in connection.execute("SELECT name FROM categories ORDER BY name")]


def authenticate(login: str) -> sqlite3.Row | None:
    with get_connection() as connection:
        return connection.execute(
            """SELECT u.user_id, u.last_name, u.first_name, u.patronymic, u.login, r.name AS role
               FROM users u JOIN roles r ON r.role_id=u.role_id WHERE u.login=?""", (login.strip(),)
        ).fetchone()

