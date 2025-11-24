SELECT DISTINCT
    u.given_name || ' ' || u.surname AS member_name,
    u.email,
    m.house_rules
FROM member m
JOIN users u ON m.member_user_id = u.user_id
JOIN address a ON m.member_user_id = a.member_user_id
JOIN job j ON m.member_user_id = j.member_user_id
WHERE j.required_caregiving_type = 'Elderly Care'
    AND a.town = 'Astana'
    AND m.house_rules ILIKE '%No pets.%';
