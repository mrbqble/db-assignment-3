SELECT
    AVG(c.hourly_rate * a.work_hours) AS average_pay
FROM APPOINTMENT a
JOIN CAREGIVER c ON a.caregiver_user_id = c.caregiver_user_id
WHERE a.status = 'accepted';