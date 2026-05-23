CREATE DATABASE IF NOT EXISTS outbreak;

CREATE TABLE IF NOT EXISTS outbreak.outbreak_signals
(
    event_id String,
    run_id Nullable(String),
    timestamp DateTime,
    zip LowCardinality(String),
    symptom LowCardinality(String),
    source_type LowCardinality(String),
    source_url Nullable(String),
    evidence_text String,
    confidence Float32,
    synthetic Bool,
    hour DateTime MATERIALIZED toStartOfHour(timestamp),
    day Date MATERIALIZED toDate(timestamp)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (zip, symptom, timestamp)
TTL timestamp + INTERVAL 180 DAY;

CREATE TABLE IF NOT EXISTS outbreak.alerts
(
    alert_id String,
    run_id String,
    created_at DateTime,
    zip LowCardinality(String),
    symptom LowCardinality(String),
    recent_count UInt32,
    baseline_avg Float32,
    baseline_stddev Float32,
    z_score Float32,
    clinical_status LowCardinality(String),
    clinical_aggregate_count UInt32,
    source_count UInt32,
    source_diversity UInt32,
    source_urls Array(String),
    decision_reason String,
    datadog_trace_id Nullable(String),
    senso_url Nullable(String),
    payment_status LowCardinality(String)
)
ENGINE = MergeTree
ORDER BY (created_at, zip, symptom);
