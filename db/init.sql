-- Archivo: db/init.sql
-- Descripción: Esquema de la base de datos MySQL para la aplicación médica.

-- Creación de la base de datos
CREATE DATABASE IF NOT EXISTS app_medica;
USE app_medica;

-- 1. Tabla de Usuarios (users)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL, -- Se guarda el hash, no la contraseña plana
    role ENUM('patient', 'doctor') NOT NULL
);

-- 2. Tabla de Doctores (doctors)
-- Almacena información adicional para los usuarios que son doctores.
CREATE TABLE IF NOT EXISTS doctors (
    user_id INT PRIMARY KEY, -- Clave foránea a users.id
    specialty VARCHAR(100) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 3. Tabla de Citas (appointments)
CREATE TABLE IF NOT EXISTS appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_date DATETIME NOT NULL,
    reason TEXT,
    status ENUM('scheduled', 'completed', 'cancelled') DEFAULT 'scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS prescriptions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  appointment_id INT NOT NULL,
  medication_name VARCHAR(120) NOT NULL,
  dose VARCHAR(80) NULL,
  route VARCHAR(40) NULL,
  frequency VARCHAR(60) NULL,
  duration VARCHAR(60) NULL,
  quantity VARCHAR(40) NULL,
  instructions TEXT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS orders (
  id INT AUTO_INCREMENT PRIMARY KEY,
  appointment_id INT NOT NULL,
  type ENUM('lab','imaging','procedure','referral') NOT NULL,
  name VARCHAR(140) NOT NULL,
  priority ENUM('normal','prioritary','urgent') DEFAULT 'normal',
  notes TEXT NULL,
  scheduled_date DATETIME NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS consult_notes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  appointment_id INT NOT NULL,
  note TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE
);

