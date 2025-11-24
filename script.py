from sqlalchemy import create_engine, text, Connection

queries: list[dict[str, str]] = [
    {
        "title": "1. Create all tables",
        "sql": """
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
    """
    },
    {
        "title": "2. Insert data into all tables",
        "sql": """
      INSERT INTO "USER" (user_id, email, given_name, surname, city, phone_number, profile_description, password) VALUES
      (1, 'arman.armanov@example.com',  'Arman',  'Armanov',  'Astana',  '+77771234567', 'Experienced caregiver and IT student.', 'pass1'),
      (2, 'amina.aminova@example.com',  'Amina',  'Aminova',  'Astana',  '+77772345678', 'Mother of two looking for help.',       'pass2'),
      (3, 'bota.baimen@example.com',    'Bota',   'Baimen',   'Astana',  '+77773456789', 'Professional nurse.',                   'pass3'),
      (4, 'daniyar.duisen@example.com', 'Daniyar','Duisen',   'Almaty',  '+77774567890', 'Student offering babysitting.',         'pass4'),
      (5, 'saltanat.serik@example.com', 'Saltanat','Serik',   'Astana',  '+77775678901', 'Needs help caring for grandmother.',    'pass5'),
      (6, 'ivan.ivanov@example.com',    'Ivan',   'Ivanov',   'Astana',  '+77776789012', 'Part-time caregiver.',                  'pass6'),
      (7, 'aliya.akhmet@example.com',   'Aliya',  'Akhmet',   'Astana',  '+77777890123', 'Special needs care experience.',        'pass7'),
      (8, 'john.doe@example.com',       'John',   'Doe',      'Shymkent','+77778901234', 'Babysitter with flexible schedule.',    'pass8'),
      (9, 'mary.jane@example.com',      'Mary',   'Jane',     'Astana',  '+77779012345', 'Nurse and babysitter.',                 'pass9'),
      (10,'timur.tolegen@example.com',  'Timur',  'Tolegen',  'Almaty',  '+77770123456', 'Looking for caregiver for grandparents.','pass10');

      INSERT INTO CAREGIVER (caregiver_user_id, photo, gender, caregiving_type, hourly_rate) VALUES
      (1,  'arman.jpg',   'Male',   'Elderly Care', 12.00),
      (2,  'amina.jpg',   'Female', 'Babysitter',    9.50),
      (3,  'bota.jpg',    'Female', 'Elderly Care', 15.00),
      (4,  'daniyar.jpg', 'Male',   'Babysitter',    8.00),
      (5,  'saltanat.jpg','Female', 'Elderly Care', 11.00),
      (6,  'ivan.jpg',    'Male',   'Babysitter',   10.00),
      (7,  'aliya.jpg',   'Female', 'Special Needs',16.00),
      (8,  'john.jpg',    'Male',   'Babysitter',    7.50),
      (9,  'mary.jpg',    'Female', 'Babysitter',   13.00),
      (10, 'timur.jpg',   'Male',   'Elderly Care', 10.50);

      INSERT INTO MEMBER (member_user_id, house_rules, dependent_description) VALUES
      (1,  'No smoking. Quiet after 22:00.',                'Elderly father with mobility issues.'),
      (2,  'No pets. Quiet after 21:00.',                   'Toddler and baby at home.'),
      (3,  'No pets. No smoking.',                          'Elderly mother with dementia.'),
      (4,  'No alcohol allowed.',                           'Younger brother needing tutoring and supervision.'),
      (5,  'No pets. Quiet after 20:00.',                   'Grandmother with limited mobility.'),
      (6,  'No shoes inside.',                              'Two kids aged 5 and 8.'),
      (7,  'No pets. Quiet home.',                          'Child with autism requiring routine.'),
      (8,  'No smoking. Pets allowed.',                     'Infant care needed in the evenings.'),
      (9,  'No loud music after 20:00.',                    'Newborn twins requiring night care.'),
      (10, 'No pets. No smoking; quiet neighborhood.',      'Grandparents requiring daily assistance.');

      INSERT INTO ADDRESS (member_user_id, house_number, street, town) VALUES
      (1,  '10',  'Kabanbay Batyr', 'Astana'),
      (2,  '15A', 'Kabanbay Batyr', 'Astana'),
      (3,  '25',  'Abai',           'Astana'),
      (4,  '5',   'Satpayev',       'Almaty'),
      (5,  '12',  'Kabanbay Batyr', 'Astana'),
      (6,  '7',   'Saryarka',       'Astana'),
      (7,  '19',  'Abai',           'Astana'),
      (8,  '3',   'Turan',          'Astana'),
      (9,  '8',   'Al-Farabi',      'Almaty'),
      (10, '30',  'Saryarka',       'Astana');

      INSERT INTO JOB (job_id, member_user_id, required_caregiving_type, other_requirements, date_posted) VALUES
      (1,  2,  'Babysitter', 'Soft-spoken, patient, help with homework for two children.', '2025-01-10'),
      (2,  3,  'Elderly Care', 'Soft-spoken and experienced with dementia care.', '2025-01-12'),
      (3,  1,  'Elderly Care', 'Can cook healthy meals and monitor medications.', '2025-01-15'),
      (4,  5,  'Elderly Care', 'Strong enough to assist with transfers; respectful and punctual.', '2025-01-18'),
      (5,  6,  'Babysitter', 'Soft-spoken, can drive children to activities and help with homework.', '2025-01-20'),
      (6,  7,  'Special Needs', 'Experience with autism, very soft-spoken and structured.', '2025-01-22'),
      (7,  8,  'Babysitter', 'Comfortable with pets; flexible evening hours.', '2025-01-24'),
      (8,  9,  'Babysitter', 'Can manage twins, calm under pressure.', '2025-01-26'),
      (9,  10, 'Elderly Care', 'Night shifts, responsible, basic first-aid knowledge.', '2025-01-28'),
      (10, 3,  'Elderly Care', 'Soft-spoken, can track medications and accompany to clinics.', '2025-02-01');

      INSERT INTO JOB_APPLICATION (caregiver_user_id, job_id, date_applied) VALUES
      (1,  2,  '2025-01-13'),
      (3,  2,  '2025-01-14'),
      (4,  1,  '2025-01-11'),
      (6,  1,  '2025-01-11'),
      (5,  3,  '2025-01-16'),
      (7,  6,  '2025-01-23'),
      (8,  5,  '2025-01-21'),
      (9,  5,  '2025-01-21'),
      (2,  7,  '2025-01-25'),
      (4,  7,  '2025-01-25'),
      (3,  9,  '2025-01-29'),
      (10, 9,  '2025-01-29'),
      (6,  8,  '2025-01-27');

      INSERT INTO APPOINTMENT (appointment_id, caregiver_user_id, member_user_id, appointment_date, appointment_time, work_hours, status) VALUES
      (1,  3,  3,  '2025-02-05', '09:00', 4.0, 'accepted'),
      (2,  1,  1,  '2025-02-06', '10:00', 3.5, 'accepted'),
      (3,  4,  2,  '2025-02-07', '18:00', 5.0, 'accepted'),
      (4,  6,  6,  '2025-02-08', '14:00', 2.5, 'pending'),
      (5,  7,  7,  '2025-02-09', '08:00', 6.0, 'accepted'),
      (6,  8,  8,  '2025-02-10', '19:00', 4.0, 'cancelled'),
      (7,  9,  9,  '2025-02-11', '13:00', 3.0, 'accepted'),
      (8,  5,  5,  '2025-02-12', '09:30', 2.0, 'accepted'),
      (9,  2,  2,  '2025-02-13', '15:00', 4.5, 'pending'),
      (10, 10, 10, '2025-02-14', '17:00', 5.5, 'accepted');
    """
    },
    {
        "title": "3.1 Update phone number of Arman Armanov to +77773414141",
        "sql": """
      UPDATE "USER"
      SET phone_number = '+77773414141'
      WHERE given_name = 'Arman' AND surname = 'Armanov';
    """
    },
    {
        "title": "3.2 Add $0.3 commission if rate < $10, or 10% if >= $10",
        "sql": """
      UPDATE CAREGIVER
      SET hourly_rate = CASE
          WHEN hourly_rate < 10 THEN hourly_rate + 0.3
          ELSE hourly_rate * 1.10
      END;
    """
    },
    {
        "title": "4.1 Delete jobs posted by Amina Aminova",
        "sql": """
      DELETE FROM JOB
      WHERE member_user_id IN (
          SELECT member_user_id
          FROM MEMBER
          WHERE member_user_id IN (
              SELECT user_id
              FROM "USER"
              WHERE given_name = 'Amina' AND surname = 'Aminova'
          )
      );
    """
    },
    {
        "title": "4.2 Delete all members who live on Kabanbay Batyr street",
        "sql": """
      DELETE FROM MEMBER
      WHERE member_user_id IN (
          SELECT member_user_id
          FROM ADDRESS
          WHERE street = 'Kabanbay Batyr'
      );
    """
    },
    {
        "title": "5.1 Select caregiver and member names for accepted appointments",
        "sql": """
      SELECT
          cg_user.given_name || ' ' || cg_user.surname AS caregiver_name,
          m_user.given_name || ' ' || m_user.surname AS member_name
      FROM APPOINTMENT a
      JOIN "USER" cg_user ON a.caregiver_user_id = cg_user.user_id
      JOIN "USER" m_user ON a.member_user_id = m_user.user_id
      WHERE a.status = 'accepted';
    """
    },
    {
        "title": "5.2 List job ids that contain 'soft-spoken' in other requirements",
        "sql": """
      SELECT job_id
      FROM JOB
      WHERE other_requirements ILIKE '%soft-spoken%';
    """
    },
    {
        "title": "5.3 List work hours of all babysitter positions",
        "sql": """
      SELECT a.appointment_id, a.work_hours
      FROM APPOINTMENT a
      JOIN CAREGIVER c ON a.caregiver_user_id = c.caregiver_user_id
      WHERE c.caregiving_type = 'Babysitter';
    """
    },
    {
        "title": "5.4 List members looking for Elderly Care in Astana with 'No pets.' rule",
        "sql": """
      SELECT DISTINCT
          u.given_name || ' ' || u.surname AS member_name,
          u.email,
          m.house_rules
      FROM MEMBER m
      JOIN "USER" u ON m.member_user_id = u.user_id
      JOIN ADDRESS a ON m.member_user_id = a.member_user_id
      JOIN JOB j ON m.member_user_id = j.member_user_id
      WHERE j.required_caregiving_type = 'Elderly Care'
          AND a.town = 'Astana'
          AND m.house_rules ILIKE '%No pets.%';
    """
    },
    {
        "title": "6.1 Count applicants for each job posted by a member",
        "sql": """
      SELECT
          j.job_id,
          u.given_name || ' ' || u.surname AS member_name,
          COUNT(ja.caregiver_user_id) AS applicant_count
      FROM JOB j
      JOIN MEMBER m ON j.member_user_id = m.member_user_id
      JOIN "USER" u ON m.member_user_id = u.user_id
      LEFT JOIN JOB_APPLICATION ja ON j.job_id = ja.job_id
      GROUP BY j.job_id, u.given_name, u.surname
      ORDER BY j.job_id;
    """
    },
    {
        "title": "6.2 Total hours spent by caregivers for all accepted appointments",
        "sql": """
      SELECT
          cg_user.given_name || ' ' || cg_user.surname AS caregiver_name,
          SUM(a.work_hours) AS total_hours
      FROM APPOINTMENT a
      JOIN CAREGIVER c ON a.caregiver_user_id = c.caregiver_user_id
      JOIN "USER" cg_user ON c.caregiver_user_id = cg_user.user_id
      WHERE a.status = 'accepted'
      GROUP BY cg_user.given_name, cg_user.surname
      ORDER BY total_hours DESC;
    """
    },
    {
        "title": "6.3 Average pay of caregivers based on accepted appointments",
        "sql": """
      SELECT
          AVG(c.hourly_rate * a.work_hours) AS average_pay
      FROM APPOINTMENT a
      JOIN CAREGIVER c ON a.caregiver_user_id = c.caregiver_user_id
      WHERE a.status = 'accepted';
    """
    },
    {
        "title": "6.4 Caregivers who earn above average based on accepted appointments",
        "sql": """
      SELECT
          cg_user.given_name || ' ' || cg_user.surname AS caregiver_name,
          SUM(c.hourly_rate * a.work_hours) AS total_earnings
      FROM APPOINTMENT a
      JOIN CAREGIVER c ON a.caregiver_user_id = c.caregiver_user_id
      JOIN "USER" cg_user ON c.caregiver_user_id = cg_user.user_id
      WHERE a.status = 'accepted'
      GROUP BY cg_user.given_name, cg_user.surname
      HAVING SUM(c.hourly_rate * a.work_hours) > (
          SELECT AVG(c2.hourly_rate * a2.work_hours)
          FROM APPOINTMENT a2
          JOIN CAREGIVER c2 ON a2.caregiver_user_id = c2.caregiver_user_id
          WHERE a2.status = 'accepted'
      )
      ORDER BY total_earnings DESC;
    """
    },
    {
        "title": "7. Calculate the total cost to pay for a caregiver for all accepted appointments.",
        "sql": """
      SELECT
          a.appointment_id,
          cg_user.given_name || ' ' || cg_user.surname AS caregiver_name,
          m_user.given_name || ' ' || m_user.surname AS member_name,
          a.work_hours,
          c.hourly_rate,
          (c.hourly_rate * a.work_hours) AS total_cost
      FROM APPOINTMENT a
      JOIN CAREGIVER c ON a.caregiver_user_id = c.caregiver_user_id
      JOIN "USER" cg_user ON c.caregiver_user_id = cg_user.user_id
      JOIN "USER" m_user ON a.member_user_id = m_user.user_id
      WHERE a.status = 'accepted'
      ORDER BY a.appointment_id;
    """
    },
    {
        "title": "8. Create View for all job applications and the applicants.",
        "sql": """
      CREATE OR REPLACE VIEW job_applications_view AS
      SELECT
          ja.job_id,
          j.required_caregiving_type,
          j.other_requirements,
          j.date_posted,
          m_user.given_name || ' ' || m_user.surname AS job_poster_name,
          ja.caregiver_user_id,
          cg_user.given_name || ' ' || cg_user.surname AS applicant_name,
          c.caregiving_type,
          c.hourly_rate,
          ja.date_applied
      FROM JOB_APPLICATION ja
      JOIN JOB j ON ja.job_id = j.job_id
      JOIN MEMBER m ON j.member_user_id = m.member_user_id
      JOIN "USER" m_user ON m.member_user_id = m_user.user_id
      JOIN CAREGIVER c ON ja.caregiver_user_id = c.caregiver_user_id
      JOIN "USER" cg_user ON c.caregiver_user_id = cg_user.user_id;
    """
    },
    {
        "title": "8.1 Select all job applications and the applicants.",
        "sql": """
      SELECT * FROM job_applications_view
      ORDER BY job_id, date_applied;
    """
    }
]


def execute_query(conn: Connection, sql: str, title: str):
    print(f"\n{title}")
    print("-" * 80)

    try:
        result = conn.execute(text(sql))
        conn.commit()

        try:
            rows = result.fetchall()
            if rows:
                for row in rows:
                    print(row)
            else:
                print("(No results)")

        except Exception as e:
            rowCount = result.rowcount
            if rowCount > 0:
                print(f"  Rows affected: {rowCount}")
            else:
                print("(No rows affected)")
        print("✓ Query executed successfully!")
    except Exception as e:
        conn.rollback()
        print(f"✗ Error: {str(e)}")


def main():
    database_url = "postgresql+psycopg://postgres:2148@localhost:5432/db-assignment"

    try:
        engine = create_engine(database_url)
        print(f"\nConnecting to database...")

        with engine.connect() as conn:
            print("✓ Connected successfully!\n")

            for query in queries:
                execute_query(conn, query["sql"], query["title"])

            print("\n" + "="*80)
            print("  All queries completed!")
            print("="*80)

    except Exception as e:
        print(f"\n✗ Connection error: {str(e)}")
        print("\nMake sure that:")
        print(f"  1. Database server is running at {database_url}")
        print("  2. Connection credentials are correct")


if __name__ == '__main__':
    main()
