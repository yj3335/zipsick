-- anomaly.sql
-- Detects ZIP/symptom pairs with statistically elevated recent counts.
-- Parameterised via string replacement in anomaly/engine.py (z_score >= 2.5 / recent_count >= 5).

WITH
recent AS
(
    SELECT
        zip,
        symptom,
        count() AS recent_count,
        count() AS source_count,
        uniqExact(source_type) AS source_diversity,
        groupArrayDistinct(ifNull(source_url, '')) AS source_urls
    FROM outbreak.outbreak_signals
    WHERE timestamp > now() - INTERVAL 6 HOUR
    GROUP BY zip, symptom
),
baseline AS
(
    SELECT
        zip,
        symptom,
        avg(cnt) AS baseline_avg,
        stddevPop(cnt) AS baseline_stddev
    FROM
    (
        SELECT zip, symptom, toStartOfHour(timestamp) AS hour, count() AS cnt
        FROM outbreak.outbreak_signals
        WHERE timestamp BETWEEN now() - INTERVAL 90 DAY AND now() - INTERVAL 6 HOUR
        GROUP BY zip, symptom, hour
    )
    GROUP BY zip, symptom
)
SELECT
    recent.zip,
    recent.symptom,
    recent.recent_count,
    recent.source_count,
    recent.source_diversity,
    recent.source_urls,
    baseline.baseline_avg,
    greatest(baseline.baseline_stddev, 1.0) AS baseline_stddev,
    round(
        (recent.recent_count - baseline.baseline_avg) / greatest(baseline.baseline_stddev, 1.0),
        2
    ) AS z_score
FROM recent
INNER JOIN baseline USING (zip, symptom)
WHERE recent.recent_count >= 5
  AND z_score >= 2.5
ORDER BY z_score DESC;
