SELECT
    cg_user.given_name || ' ' || cg_user.surname AS caregiver_name,
    m_user.given_name || ' ' || m_user.surname AS member_name
FROM APPOINTMENT a
JOIN "USER" cg_user ON a.caregiver_user_id = cg_user.user_id
JOIN "USER" m_user ON a.member_user_id = m_user.user_id
WHERE a.status = 'accepted';