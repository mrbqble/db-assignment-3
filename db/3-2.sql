UPDATE caregiver
SET hourly_rate = CASE
    WHEN hourly_rate < 10 THEN hourly_rate + 0.3
    ELSE hourly_rate * 1.10
END;