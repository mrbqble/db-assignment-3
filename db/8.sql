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

SELECT * FROM job_applications_view
ORDER BY job_id, date_applied;