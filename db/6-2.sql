SELECT
    CONCAT(cg_user.given_name, ' ', cg_user.surname) AS caregiver_name,
    SUM(a.work_hours) AS total_hours
FROM appointment a
JOIN caregiver c ON a.caregiver_user_id = c.caregiver_user_id
JOIN users cg_user ON c.caregiver_user_id = cg_user.user_id
WHERE a.status = 'accepted'
GROUP BY cg_user.given_name, cg_user.surname
ORDER BY total_hours DESC;