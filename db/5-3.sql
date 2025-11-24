SELECT a.appointment_id, a.work_hours
FROM APPOINTMENT a
JOIN CAREGIVER c ON a.caregiver_user_id = c.caregiver_user_id
WHERE c.caregiving_type = 'Babysitter';