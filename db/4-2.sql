DELETE FROM MEMBER
WHERE member_user_id IN (
    SELECT member_user_id
    FROM ADDRESS
    WHERE street = 'Kabanbay Batyr'
);