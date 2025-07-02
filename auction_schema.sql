-- Update users table to add user_role
ALTER TABLE users
ADD COLUMN user_role ENUM('farmer', 'dealer') NOT NULL DEFAULT 'farmer';

-- Create commodities_names table
CREATE TABLE IF NOT EXISTS commodities_names (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create districts_names table
CREATE TABLE IF NOT EXISTS districts_names (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_district_state (name, state)
);

-- Create crops_for_sale table
CREATE TABLE IF NOT EXISTS crops_for_sale (
    id INT AUTO_INCREMENT PRIMARY KEY,
    farmer_id INT NOT NULL,
    commodity_id INT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    unit ENUM('kg', 'quintal', 'ton') NOT NULL DEFAULT 'kg',
    base_price DECIMAL(10,2) NOT NULL,
    district_id INT NOT NULL,
    expected_date DATE NOT NULL,
    image_path VARCHAR(255),
    description TEXT,
    status ENUM('active', 'closed', 'sold') NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (farmer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (commodity_id) REFERENCES commodities_names(id),
    FOREIGN KEY (district_id) REFERENCES districts_names(id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- Create bids table
CREATE TABLE IF NOT EXISTS bids (
    id INT AUTO_INCREMENT PRIMARY KEY,
    crop_id INT NOT NULL,
    dealer_id INT NOT NULL,
    bid_amount DECIMAL(10,2) NOT NULL,
    status ENUM('pending', 'accepted', 'rejected') NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (crop_id) REFERENCES crops_for_sale(id) ON DELETE CASCADE,
    FOREIGN KEY (dealer_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_crop_status (crop_id, status),
    INDEX idx_dealer (dealer_id)
);
