-- Database indexes for optimization
-- These indexes improve query performance on frequently filtered/searched columns
-- Note: IF NOT EXISTS is supported in MySQL 5.7.4+ and MariaDB 10.0.5+
-- For older MySQL versions, remove IF NOT EXISTS and handle duplicate index errors manually

-- Users table indexes
CREATE INDEX IF NOT EXISTS idx_users_city ON users(city);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_phone_number ON users(phone_number);
CREATE INDEX IF NOT EXISTS idx_users_given_name ON users(given_name);
CREATE INDEX IF NOT EXISTS idx_users_surname ON users(surname);

-- Caregiver table indexes
CREATE INDEX IF NOT EXISTS idx_caregiver_type ON caregiver(caregiving_type);
CREATE INDEX IF NOT EXISTS idx_caregiver_hourly_rate ON caregiver(hourly_rate);
CREATE INDEX IF NOT EXISTS idx_caregiver_gender ON caregiver(gender);

-- Member table indexes (if needed for future queries)
-- No frequently filtered columns currently

-- Address table indexes
CREATE INDEX IF NOT EXISTS idx_address_town ON address(town);
CREATE INDEX IF NOT EXISTS idx_address_street ON address(street);

-- Job table indexes
CREATE INDEX IF NOT EXISTS idx_job_caregiving_type ON job(required_caregiving_type);
CREATE INDEX IF NOT EXISTS idx_job_date_posted ON job(date_posted);
CREATE INDEX IF NOT EXISTS idx_job_member_user_id ON job(member_user_id);

-- Job Application table indexes
CREATE INDEX IF NOT EXISTS idx_jobapp_caregiver_id ON job_application(caregiver_user_id);
CREATE INDEX IF NOT EXISTS idx_jobapp_job_id ON job_application(job_id);
CREATE INDEX IF NOT EXISTS idx_jobapp_date_applied ON job_application(date_applied);

-- Appointment table indexes
CREATE INDEX IF NOT EXISTS idx_appointment_status ON appointment(status);
CREATE INDEX IF NOT EXISTS idx_appointment_date ON appointment(appointment_date);
CREATE INDEX IF NOT EXISTS idx_appointment_time ON appointment(appointment_time);
CREATE INDEX IF NOT EXISTS idx_appointment_caregiver_id ON appointment(caregiver_user_id);
CREATE INDEX IF NOT EXISTS idx_appointment_member_id ON appointment(member_user_id);

