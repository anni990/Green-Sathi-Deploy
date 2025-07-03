-- Create the database
-- CREATE DATABASE IF NOT EXISTS farmers_chatbot;
-- USE farmers_chatbot;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    preferred_language ENUM('english', 'hindi', 'bhojpuri', 'bundelkhandi', 'marathi', 'haryanvi', 'bengali', 'tamil', 'telugu', 'kannada', 'gujarati', 'urdu', 'malayalam', 'punjabi') DEFAULT 'hindi',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL
    latitude FLOAT NULL
    longitude FLOAT NULL
);

-- Chat sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) DEFAULT 'New Chat',
    language ENUM('english', 'hindi', 'bhojpuri', 'bundelkhandi', 'marathi', 'haryanvi', 'bengali', 'tamil', 'telugu', 'kannada', 'gujarati', 'urdu', 'malayalam', 'punjabi') DEFAULT 'hindi',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    chat_id VARCHAR(36) NOT NULL,
    user_id INT NOT NULL,
    text TEXT NOT NULL,
    sender ENUM('user', 'bot') NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    input_type ENUM('text', 'voice', 'image', 'soil_report') DEFAULT 'text',
    FOREIGN KEY (chat_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Chat history table (legacy - keeping for backward compatibility)
CREATE TABLE IF NOT EXISTS chat_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    user_message TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    input_type ENUM('text', 'voice', 'image', 'soil_report') DEFAULT 'text',
    language_detected VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Plant diagnosis records
CREATE TABLE IF NOT EXISTS plant_diagnoses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    image_path VARCHAR(255) NOT NULL,
    plant_type VARCHAR(100),
    disease_name VARCHAR(100),
    confidence_score FLOAT,
    recommendation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Soil reports
CREATE TABLE IF NOT EXISTS soil_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    chat_id VARCHAR(36) NOT NULL,
    report_path VARCHAR(255) NOT NULL,
    -- village VARCHAR(100),
    district VARCHAR(100),
    state VARCHAR(100),
    ph_value FLOAT,
    ec FLOAT,
    organic_carbon FLOAT,
    phosphorus FLOAT,
    potassium FLOAT,
    zinc FLOAT,
    copper FLOAT,
    iron FLOAT,
    manganese FLOAT,
    nitrogen FLOAT,
    sulphur FLOAT,
    soil_type VARCHAR(100),
    predicted_crop VARCHAR(100),
    crop_recommendations TEXT,
    fertilizer_recommendations TEXT,
    full_fertilizer_report TEXT,
    json_fertilizer_report TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (chat_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
);

-- Mandi data table
CREATE TABLE IF NOT EXISTS mandi_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    state VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    market VARCHAR(255) NOT NULL,
    commodity VARCHAR(100) NOT NULL,
    variety VARCHAR(100),
    grade VARCHAR(50),
    arrival_date DATE NOT NULL,
    min_price DECIMAL(10,2),
    max_price DECIMAL(10,2),
    modal_price DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_state_district (state, district),
    INDEX idx_commodity (commodity),
    INDEX idx_arrival_date (arrival_date)
);

CREATE TABLE IF NOT EXISTS districts_coordinates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    district_name VARCHAR(100) NOT NULL,
    state_name VARCHAR(100) NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
);

-- Initial admin user (password: admin123)
INSERT INTO users (username, email, password_hash, preferred_language)
VALUES ('admin', 'admin@farmerchatbot.com', '$2b$12$NbADbkE8v2HOXgTtOehm7.vGCrwHpD3muS/ZyQxLLmZkL9jOvnvPi', 'english'); 