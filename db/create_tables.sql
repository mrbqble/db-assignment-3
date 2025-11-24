DROP TABLE IF EXISTS APPOINTMENT CASCADE;
DROP TABLE IF EXISTS JOB_APPLICATION CASCADE;
DROP TABLE IF EXISTS JOB CASCADE;
DROP TABLE IF EXISTS ADDRESS CASCADE;
DROP TABLE IF EXISTS MEMBER CASCADE;
DROP TABLE IF EXISTS CAREGIVER CASCADE;
DROP TABLE IF EXISTS "USER" CASCADE;

CREATE TABLE "USER" (
    user_id            SERIAL PRIMARY KEY,
    email              VARCHAR(255) UNIQUE NOT NULL,
    given_name         VARCHAR(50) NOT NULL,
    surname            VARCHAR(50) NOT NULL,
    city               VARCHAR(100),
    phone_number       VARCHAR(20),
    profile_description TEXT,
    password           VARCHAR(255) NOT NULL
);

CREATE TABLE CAREGIVER (
    caregiver_user_id  INTEGER PRIMARY KEY,
    photo              VARCHAR(255),
    gender             VARCHAR(10),
    caregiving_type    VARCHAR(50) NOT NULL,
    hourly_rate        NUMERIC(6,2) NOT NULL,
    CONSTRAINT fk_caregiver_user
        FOREIGN KEY (caregiver_user_id)
        REFERENCES "USER"(user_id)
        ON DELETE CASCADE
);

CREATE TABLE MEMBER (
    member_user_id     INTEGER PRIMARY KEY,
    house_rules        TEXT,
    dependent_description TEXT,
    CONSTRAINT fk_member_user
        FOREIGN KEY (member_user_id)
        REFERENCES "USER"(user_id)
        ON DELETE CASCADE
);

CREATE TABLE ADDRESS (
    member_user_id     INTEGER PRIMARY KEY,
    house_number       VARCHAR(10) NOT NULL,
    street             VARCHAR(100) NOT NULL,
    town               VARCHAR(100) NOT NULL,
    CONSTRAINT fk_address_member
        FOREIGN KEY (member_user_id)
        REFERENCES MEMBER(member_user_id)
        ON DELETE CASCADE
);

CREATE TABLE JOB (
    job_id                 SERIAL PRIMARY KEY,
    member_user_id         INTEGER NOT NULL,
    required_caregiving_type VARCHAR(50) NOT NULL,
    other_requirements     TEXT,
    date_posted            DATE NOT NULL,
    CONSTRAINT fk_job_member
        FOREIGN KEY (member_user_id)
        REFERENCES MEMBER(member_user_id)
        ON DELETE CASCADE
);

CREATE TABLE JOB_APPLICATION (
    caregiver_user_id  INTEGER NOT NULL,
    job_id             INTEGER NOT NULL,
    date_applied       DATE NOT NULL,
    PRIMARY KEY (caregiver_user_id, job_id),
    CONSTRAINT fk_jobapp_caregiver
        FOREIGN KEY (caregiver_user_id)
        REFERENCES CAREGIVER(caregiver_user_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_jobapp_job
        FOREIGN KEY (job_id)
        REFERENCES JOB(job_id)
        ON DELETE CASCADE
);

CREATE TABLE APPOINTMENT (
    appointment_id     SERIAL PRIMARY KEY,
    caregiver_user_id  INTEGER NOT NULL,
    member_user_id     INTEGER NOT NULL,
    appointment_date   DATE NOT NULL,
    appointment_time   TIME NOT NULL,
    work_hours         NUMERIC(4,1) NOT NULL,
    status             VARCHAR(20) NOT NULL,
    CONSTRAINT fk_appointment_caregiver
        FOREIGN KEY (caregiver_user_id)
        REFERENCES CAREGIVER(caregiver_user_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_appointment_member
        FOREIGN KEY (member_user_id)
        REFERENCES MEMBER(member_user_id)
        ON DELETE CASCADE
);