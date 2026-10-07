-- SpaceLoop Relational Database Schema
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    full_name VARCHAR(120) NOT NULL,
    role VARCHAR(20) DEFAULT 'seeker',
    is_admin BOOLEAN DEFAULT 0,
    is_verified BOOLEAN DEFAULT 0,
    mfa_enabled BOOLEAN DEFAULT 0,
    mfa_secret VARCHAR(64),
    trust_score FLOAT DEFAULT 100.0,
    student_verified BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS spaces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id INTEGER NOT NULL REFERENCES users(id),
    title VARCHAR(150) NOT NULL,
    description TEXT,
    price_per_day FLOAT NOT NULL,
    price_per_hour FLOAT,
    city VARCHAR(80) NOT NULL,
    area VARCHAR(100),
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    capacity_sqft INTEGER DEFAULT 50,
    amenities TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    space_id INTEGER NOT NULL REFERENCES spaces(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    subtotal FLOAT NOT NULL,
    platform_fee FLOAT NOT NULL,
    deposit FLOAT DEFAULT 100.0,
    total_amount FLOAT NOT NULL,
    status VARCHAR(30) DEFAULT 'confirmed',
    checkin_pin VARCHAR(6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS escrow_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL REFERENCES bookings(id),
    subtotal FLOAT NOT NULL,
    platform_fee FLOAT NOT NULL,
    deposit_amount FLOAT DEFAULT 100.0,
    status VARCHAR(30) DEFAULT 'HELD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS access_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL REFERENCES bookings(id),
    action VARCHAR(20) NOT NULL,
    verified BOOLEAN NOT NULL,
    latitude FLOAT,
    longitude FLOAT,
    method VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
