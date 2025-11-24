SELECT DISTINCT
    CONCAT(u.given_name, ' ', u.surname) AS member_name,
    u.email,
    m.house_rules
FROM member m
JOIN users u ON m.member_user_id = u.user_id
JOIN address a ON m.member_user_id = a.member_user_id
JOIN job j ON m.member_user_id = j.member_user_id
WHERE j.required_caregiving_type = 'caregiver for elderly'
    AND a.town = 'Astana'
    AND LOWER(m.house_rules) LIKE LOWER('%No pets.%');
