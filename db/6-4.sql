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