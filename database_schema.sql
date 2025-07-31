-- Database Schema for DB Optimizer Testing
-- This schema creates tables with various optimization opportunities

-- Create database (if not exists)
-- CREATE DATABASE db_optimizer_test;

-- Connect to the database
-- \c db_optimizer_test;

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Users table (small table, good for joins)
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    user_type VARCHAR(20) DEFAULT 'regular'
);

-- 2. Products table (medium table, good for indexing)
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    category_id INTEGER,
    brand VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_available BOOLEAN DEFAULT TRUE,
    stock_quantity INTEGER DEFAULT 0
);

-- 3. Categories table (small lookup table)
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_category_id INTEGER REFERENCES categories(category_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Orders table (large table, good for partitioning)
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(12,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    shipping_address TEXT,
    billing_address TEXT,
    payment_method VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Order_items table (very large table, good for complex joins)
CREATE TABLE order_items (
    item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Reviews table (medium table, good for text search)
CREATE TABLE reviews (
    review_id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(product_id),
    user_id INTEGER REFERENCES users(user_id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(200),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    helpful_votes INTEGER DEFAULT 0
);

-- 7. Inventory_log table (very large table, good for time-based partitioning)
CREATE TABLE inventory_log (
    log_id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(product_id),
    action_type VARCHAR(20) NOT NULL, -- 'in', 'out', 'adjustment'
    quantity_change INTEGER NOT NULL,
    previous_quantity INTEGER,
    new_quantity INTEGER,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. User_sessions table (large table, good for time-series analysis)
CREATE TABLE user_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER REFERENCES users(user_id),
    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_end TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    pages_visited INTEGER DEFAULT 0,
    total_duration_seconds INTEGER
);

-- Add foreign key constraints
ALTER TABLE products ADD CONSTRAINT fk_products_category 
    FOREIGN KEY (category_id) REFERENCES categories(category_id);

-- Create indexes for common query patterns
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_reviews_product_id ON reviews(product_id);
CREATE INDEX idx_reviews_user_id ON reviews(user_id);
CREATE INDEX idx_reviews_rating ON reviews(rating);
CREATE INDEX idx_inventory_log_product_id ON inventory_log(product_id);
CREATE INDEX idx_inventory_log_created_at ON inventory_log(created_at);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_start ON user_sessions(session_start);

-- Create composite indexes for common join patterns
CREATE INDEX idx_orders_user_date ON orders(user_id, order_date);
CREATE INDEX idx_order_items_order_product ON order_items(order_id, product_id);
CREATE INDEX idx_reviews_product_rating ON reviews(product_id, rating);

-- Create partial indexes for filtered queries
CREATE INDEX idx_orders_active ON orders(user_id) WHERE status != 'cancelled';
CREATE INDEX idx_products_available ON products(product_id, name) WHERE is_available = TRUE;
CREATE INDEX idx_reviews_helpful ON reviews(review_id) WHERE helpful_votes > 10;

-- Insert sample data
-- Users (1000 records)
INSERT INTO users (username, email, first_name, last_name, user_type)
SELECT 
    'user_' || i,
    'user_' || i || '@example.com',
    'First' || i,
    'Last' || i,
    CASE WHEN i % 10 = 0 THEN 'premium' ELSE 'regular' END
FROM generate_series(1, 1000) i;

-- Categories (50 records)
INSERT INTO categories (name, description)
VALUES 
    ('Electronics', 'Electronic devices and accessories'),
    ('Clothing', 'Apparel and fashion items'),
    ('Books', 'Books and publications'),
    ('Home & Garden', 'Home improvement and garden supplies'),
    ('Sports', 'Sports equipment and accessories'),
    ('Automotive', 'Car parts and accessories'),
    ('Health & Beauty', 'Health and beauty products'),
    ('Toys & Games', 'Toys and games for all ages'),
    ('Food & Beverages', 'Food and drink products'),
    ('Jewelry', 'Jewelry and accessories');

-- Products (5000 records)
INSERT INTO products (name, description, price, category_id, brand, stock_quantity)
SELECT 
    'Product ' || i,
    'Description for product ' || i,
    (random() * 1000 + 10)::DECIMAL(10,2),
    (i % 10) + 1,
    'Brand ' || (i % 20 + 1),
    (random() * 100)::INTEGER
FROM generate_series(1, 5000) i;

-- Orders (10000 records)
INSERT INTO orders (user_id, order_date, total_amount, status)
SELECT 
    (i % 1000) + 1,
    CURRENT_TIMESTAMP - (random() * interval '365 days'),
    (random() * 500 + 10)::DECIMAL(12,2),
    CASE (i % 10)
        WHEN 0 THEN 'cancelled'
        WHEN 1 THEN 'pending'
        WHEN 2 THEN 'processing'
        ELSE 'completed'
    END
FROM generate_series(1, 10000) i;

-- Order items (50000 records)
INSERT INTO order_items (order_id, product_id, quantity, unit_price, total_price)
SELECT 
    (i % 10000) + 1,
    (i % 5000) + 1,
    (random() * 5 + 1)::INTEGER,
    (random() * 100 + 5)::DECIMAL(10,2),
    (random() * 500 + 10)::DECIMAL(10,2)
FROM generate_series(1, 50000) i;

-- Reviews (15000 records)
INSERT INTO reviews (product_id, user_id, rating, title, comment, helpful_votes)
SELECT 
    (i % 5000) + 1,
    (i % 1000) + 1,
    FLOOR(random() * 5) + 1,
    'Review ' || i,
    'This is a review comment for product ' || i,
    (random() * 50)::INTEGER
FROM generate_series(1, 15000) i;

-- Inventory log (100000 records)
INSERT INTO inventory_log (product_id, action_type, quantity_change, previous_quantity, new_quantity, reason)
SELECT 
    (i % 5000) + 1,
    CASE (i % 3)
        WHEN 0 THEN 'in'
        WHEN 1 THEN 'out'
        ELSE 'adjustment'
    END,
    (random() * 20 - 10)::INTEGER,
    (random() * 100)::INTEGER,
    (random() * 100)::INTEGER,
    'Inventory adjustment reason ' || i
FROM generate_series(1, 100000) i;

-- User sessions (25000 records)
INSERT INTO user_sessions (user_id, session_start, session_end, ip_address, pages_visited, total_duration_seconds)
SELECT 
    (i % 1000) + 1,
    CURRENT_TIMESTAMP - (random() * interval '30 days'),
    CURRENT_TIMESTAMP - (random() * interval '30 days') + interval '1 hour',
    ('192.168.1.' || (i % 255 + 1)::TEXT)::INET,
    (random() * 20 + 1)::INTEGER,
    (random() * 3600 + 60)::INTEGER
FROM generate_series(1, 25000) i;

-- Update statistics for better query planning
ANALYZE; 
