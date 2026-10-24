-- ==========================================================
-- EMI MANAGEMENT SYSTEM - DATABASE CREATION & SCHEMA SCRIPT
-- Database: emi_management_db
-- Target: MySQL 5.7+ / MySQL 8.0+
-- ==========================================================

CREATE DATABASE IF NOT EXISTS emi_management_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE emi_management_db;

-- 1. USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. LOANS TABLE
CREATE TABLE IF NOT EXISTS loans (
    loan_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    loan_name VARCHAR(100) NOT NULL,
    lender_name VARCHAR(100) NOT NULL,
    principal_amount DECIMAL(12, 2) NOT NULL,
    annual_interest_rate DECIMAL(5, 2) NOT NULL,
    tenure_months INT NOT NULL,
    emi_amount DECIMAL(12, 2) NOT NULL,
    start_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_loans_user FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    INDEX idx_loan_user (user_id),
    INDEX idx_loan_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. EMI SCHEDULE TABLE
CREATE TABLE IF NOT EXISTS emi_schedule (
    emi_id INT AUTO_INCREMENT PRIMARY KEY,
    loan_id INT NOT NULL,
    installment_number INT NOT NULL,
    due_date DATE NOT NULL,
    principal_component DECIMAL(12, 2) NOT NULL,
    interest_component DECIMAL(12, 2) NOT NULL,
    emi_amount DECIMAL(12, 2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    CONSTRAINT fk_emi_loan FOREIGN KEY (loan_id)
        REFERENCES loans(loan_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT uq_loan_installment UNIQUE (loan_id, installment_number),
    INDEX idx_emi_loan (loan_id),
    INDEX idx_emi_due_date (due_date),
    INDEX idx_emi_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. PAYMENTS TABLE
CREATE TABLE IF NOT EXISTS payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    emi_id INT NOT NULL,
    amount_paid DECIMAL(12, 2) NOT NULL,
    payment_date DATE NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    reference_number VARCHAR(100) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_payments_emi FOREIGN KEY (emi_id)
        REFERENCES emi_schedule(emi_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    INDEX idx_payments_emi (emi_id),
    INDEX idx_payment_date (payment_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
