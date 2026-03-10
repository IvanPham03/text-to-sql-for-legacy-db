from prometheus_client import Gauge, Histogram, Summary

# Metrics for Schema Sync
schema_sync_duration_seconds = Summary(
    "schema_sync_duration_seconds",
    "Time spent performing schema sync operations",
    ["sync_type"],  # e.g., 'full', 'incremental', 'cleanup'
)

schema_vectors_total = Gauge(
    "schema_vectors_total",
    "Total number of schema vectors in Qdrant",
    ["type"],  # 'table' or 'column'
)

schema_embedding_latency = Histogram(
    "schema_embedding_latency",
    "Latency of embedding generation for schema elements",
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
