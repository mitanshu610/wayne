from prometheus_client import Counter, Histogram
from prometheus_client import CollectorRegistry

REGISTRY = CollectorRegistry()
buckets = [0.1, 0.25, 0.5, 0.75, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12.5, 15, 20, 25, 30, 60]


# Database Metrics
DB_QUERY_LATENCY = Histogram(
    'wayne_db_query_received_duration_seconds',
    'Query Latency',
    ['query',"service_name"],
    registry=REGISTRY,
    buckets=buckets
)

SLOW_QUERIES_COUNTER = Counter(
    'db_slow_queries_total',
    'Total number of slow queries',
    ['query_type',"service_name"],
    registry=REGISTRY
)

FAILED_QUERIES_COUNTER = Counter(
    'db_failed_queries_total',
    'Total number of failed database queries',
    ['query_type',"service_name"],
    registry=REGISTRY
)

DEADLOCK_COUNTER = Counter(
    'db_deadlocks_total',
    'Total number of deadlocks encountered',
    ['query',"service_name"],
    registry=REGISTRY
)

# Kafka metrics

