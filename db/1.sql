
DROP TABLE IF EXISTS appointment;
DROP TABLE IF EXISTS job_application;
DROP TABLE IF EXISTS job;
DROP TABLE IF EXISTS address;
DROP TABLE IF EXISTS member;
DROP TABLE IF EXISTS caregiver;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id            INT AUTO_INCREMENT PRIMARY KEY,
    email              VARCHAR(255) UNIQUE NOT NULL,
    given_name         VARCHAR(50) NOT NULL,
    surname            VARCHAR(50) NOT NULL,
    city               VARCHAR(100),
    phone_number       VARCHAR(20) UNIQUE NOT NULL,
    profile_description TEXT,
    password           VARCHAR(255) NOT NULL
);

CREATE TABLE caregiver (
    caregiver_user_id  INTEGER PRIMARY KEY,
    photo              VARCHAR(255),
    gender             VARCHAR(10),
    caregiving_type    VARCHAR(50) NOT NULL,
    hourly_rate        NUMERIC(6,2) NOT NULL,
    CONSTRAINT fk_caregiver_user
        FOREIGN KEY (caregiver_user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,
    CONSTRAINT check_caregiving_type
        CHECK (caregiving_type IN ('babysitter', 'caregiver for elderly', 'playmate for children')),
    CONSTRAINT check_hourly_rate_positive
        CHECK (hourly_rate > 0)
);

CREATE TABLE member (
    member_user_id     INTEGER PRIMARY KEY,
    house_rules        TEXT,
    dependent_description TEXT,
    CONSTRAINT fk_member_user
        FOREIGN KEY (member_user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);

CREATE TABLE address (
    member_user_id     INTEGER PRIMARY KEY,
    house_number       VARCHAR(10) NOT NULL,
    street             VARCHAR(100) NOT NULL,
    town               VARCHAR(100) NOT NULL,
    CONSTRAINT fk_address_member
        FOREIGN KEY (member_user_id)
        REFERENCES member(member_user_id)
        ON DELETE CASCADE
);

CREATE TABLE job (
    job_id                 INT AUTO_INCREMENT PRIMARY KEY,
    member_user_id         INTEGER NOT NULL,
    required_caregiving_type VARCHAR(50) NOT NULL,
    other_requirements     TEXT,
    date_posted            DATE NOT NULL DEFAULT (CURRENT_DATE),
    CONSTRAINT fk_job_member
        FOREIGN KEY (member_user_id)
        REFERENCES member(member_user_id)
        ON DELETE CASCADE,
    CONSTRAINT check_required_caregiving_type
        CHECK (required_caregiving_type IN ('babysitter', 'caregiver for elderly', 'playmate for children'))
);

CREATE TABLE job_application (
    caregiver_user_id  INTEGER NOT NULL,
    job_id             INTEGER NOT NULL,
    date_applied       DATE NOT NULL DEFAULT (CURRENT_DATE),
    PRIMARY KEY (caregiver_user_id, job_id),
    CONSTRAINT fk_jobapp_caregiver
        FOREIGN KEY (caregiver_user_id)
        REFERENCES caregiver(caregiver_user_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_jobapp_job
        FOREIGN KEY (job_id)
        REFERENCES job(job_id)
        ON DELETE CASCADE
);

CREATE TABLE appointment (
    appointment_id     INT AUTO_INCREMENT PRIMARY KEY,
    caregiver_user_id  INTEGER NOT NULL,
    member_user_id     INTEGER NOT NULL,
    appointment_date   DATE NOT NULL,
    appointment_time   TIME NOT NULL,
    work_hours         NUMERIC(4,1) NOT NULL,
    status             VARCHAR(20) NOT NULL DEFAULT 'pending',
    CONSTRAINT fk_appointment_caregiver
        FOREIGN KEY (caregiver_user_id)
        REFERENCES caregiver(caregiver_user_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_appointment_member
        FOREIGN KEY (member_user_id)
        REFERENCES member(member_user_id)
        ON DELETE CASCADE,
    CONSTRAINT check_appointment_status
        CHECK (status IN ('pending', 'accepted', 'declined')),
    CONSTRAINT check_work_hours_positive
        CHECK (work_hours > 0 AND work_hours <= 24)
);