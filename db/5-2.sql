SELECT job_id
FROM job
WHERE LOWER(other_requirements) LIKE LOWER('%soft-spoken%');