DROP TABLE IF EXISTS daily_load_duration;

CREATE TABLE daily_load_duration AS
SELECT
    driver_name,
    ticket_date::date AS day,
    COUNT(*) AS trips,
    EXTRACT(EPOCH FROM (MAX(end_date) - MIN(start_date))) / 60.0 / COUNT(*) AS avg_load_duration_minutes
FROM tickets
WHERE ticket_status IN ('LOADED_IN_PROGRESS', 'inprogress')
GROUP BY driver_name, day
ORDER BY day;
