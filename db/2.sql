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
(1,  2,  'Babysitter',
     'Soft-spoken, patient, help with homework for two children.',
     '2025-01-10'),
(2,  3,  'Elderly Care',
     'Soft-spoken and experienced with dementia care.',
     '2025-01-12'),
(3,  1,  'Elderly Care',
     'Can cook healthy meals and monitor medications.',
     '2025-01-15'),
(4,  5,  'Elderly Care',
     'Strong enough to assist with transfers; respectful and punctual.',
     '2025-01-18'),
(5,  6,  'Babysitter',
     'Soft-spoken, can drive children to activities and help with homework.',
     '2025-01-20'),
(6,  7,  'Special Needs',
     'Experience with autism, very soft-spoken and structured.',
     '2025-01-22'),
(7,  8,  'Babysitter',
     'Comfortable with pets; flexible evening hours.',
     '2025-01-24'),
(8,  9,  'Babysitter',
     'Can manage twins, calm under pressure.',
     '2025-01-26'),
(9,  10, 'Elderly Care',
     'Night shifts, responsible, basic first-aid knowledge.',
     '2025-01-28'),
(10, 3,  'Elderly Care',
     'Soft-spoken, can track medications and accompany to clinics.',
     '2025-02-01');

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

INSERT INTO APPOINTMENT (appointment_id, caregiver_user_id, member_user_id,
                         appointment_date, appointment_time, work_hours, status)
VALUES
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