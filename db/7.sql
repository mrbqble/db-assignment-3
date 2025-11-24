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