DELETE FROM JOB
WHERE member_user_id IN (
    SELECT member_user_id
    FROM MEMBER
    WHERE member_user_id IN (
        SELECT user_id
        FROM "USER"
        WHERE given_name = 'Amina' AND surname = 'Aminova'
    )
);