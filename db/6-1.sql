SELECT
    j.job_id,
    CONCAT(u.given_name, ' ', u.surname) AS member_name,
    COUNT(ja.caregiver_user_id) AS applicant_count
FROM job j
JOIN member m ON j.member_user_id = m.member_user_id
JOIN users u ON m.member_user_id = u.user_id
LEFT JOIN job_application ja ON j.job_id = ja.job_id
GROUP BY j.job_id, u.given_name, u.surname
ORDER BY j.job_id;