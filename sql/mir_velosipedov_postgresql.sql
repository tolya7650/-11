-- PostgreSQL 17: structure for topic 3 "Мир велосипедов".
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);
CREATE TABLE subcategories (
    subcategory_id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES categories(category_id),
    name VARCHAR(100) NOT NULL,
    UNIQUE(category_id, name)
);
CREATE TABLE manufacturers (
    manufacturer_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);
CREATE TABLE variants (
    variant_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES categories(category_id),
    subcategory_id INTEGER NOT NULL REFERENCES subcategories(subcategory_id),
    manufacturer_id INTEGER NOT NULL REFERENCES manufacturers(manufacturer_id),
    image_name VARCHAR(255),
    name VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    composition TEXT NOT NULL,
    base_price NUMERIC(12,2) NOT NULL CHECK(base_price > 0),
    UNIQUE(name, manufacturer_id)
);
CREATE TABLE stock_items (
    stock_item_id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    variant_id INTEGER NOT NULL REFERENCES variants(variant_id),
    quantity INTEGER NOT NULL CHECK(quantity >= 0),
    price NUMERIC(12,2) NOT NULL CHECK(price > 0),
    UNIQUE(product_id, variant_id)
);
CREATE TABLE roles (
    role_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    last_name VARCHAR(80) NOT NULL,
    first_name VARCHAR(80) NOT NULL,
    patronymic VARCHAR(80),
    login VARCHAR(50) NOT NULL UNIQUE,
    role_id INTEGER NOT NULL REFERENCES roles(role_id)
);
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    order_date DATE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(user_id)
);
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id),
    stock_item_id INTEGER NOT NULL REFERENCES stock_items(stock_item_id),
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    unit_price NUMERIC(12,2) NOT NULL CHECK(unit_price > 0)
);

