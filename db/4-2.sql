DELETE FROM member
WHERE member_user_id IN (
    SELECT member_user_id
    FROM address
    WHERE street = 'Kabanbay Batyr'
);