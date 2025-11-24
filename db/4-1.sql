DELETE FROM job
WHERE member_user_id IN (
    SELECT member_user_id
    FROM member
    WHERE member_user_id IN (
        SELECT user_id
        FROM users
        WHERE given_name = 'Amina' AND surname = 'Aminova'
    )
);