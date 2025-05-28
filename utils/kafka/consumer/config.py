"""Configuration for consumer."""
from config.settings import loaded_config
from utils.kafka.constants import FEX_PAYMENTS_GROUP_ID, KAFKA_SERVICE_CONFIG_MAPPING, PR_EVENT_EMITTER, \
    PR_COMMENT_GENERATOR, WEB_PAGE_CRAWLER, WEB_PAGE_INDEXER
from utils.kafka.producer.config import KafkaServices

KAFKA_SERIALIZATION_FORMAT = "json"
KAFKA_SESSION_TIMEOUT_IN_MS = 20000
KAFKA_OFFSET_RESET_STRATEGY = "latest"

KAFKA_CONSUMER_SETTINGS = {}

COMMON_CONSUMER_CONFIG = {
    "bootstrap.servers": loaded_config.kafka_bootstrap_servers,
    "session.timeout.ms": KAFKA_SESSION_TIMEOUT_IN_MS,
    "default.topic.config": {"auto.offset.reset": KAFKA_OFFSET_RESET_STRATEGY},
    "group.id": FEX_PAYMENTS_GROUP_ID,
}

KAFKA_CONSUMER_CONFIG = {
    KafkaServices.payments: {
        "azure_pr_event_emitter_consumer": {
            "service_name": KafkaServices.payments,
            "deserialization_format": KAFKA_SERIALIZATION_FORMAT,
            "consumer_config": COMMON_CONSUMER_CONFIG,
            "topics_configurations": {
                KAFKA_SERVICE_CONFIG_MAPPING[KafkaServices.payments][PR_EVENT_EMITTER]["topics"][0]: {
                    "tasks": [crawler]
                }
            },
            "async_kafka": False,
        },
        "azure_pr_comment_generator_consumer": {
            "service_name": KafkaServices.payments,
            "deserialization_format": KAFKA_SERIALIZATION_FORMAT,
            "consumer_config": COMMON_CONSUMER_CONFIG,
            "topics_configurations": {
                KAFKA_SERVICE_CONFIG_MAPPING[KafkaServices.payments][PR_COMMENT_GENERATOR]["topics"][0]: {
                    "tasks": [indexer]
                }
            },
            "async_kafka": False,
        },
        "docs_rag_crawler": {
            "service_name": KafkaServices.payments,
            "deserialization_format": KAFKA_SERIALIZATION_FORMAT,
            "consumer_config": COMMON_CONSUMER_CONFIG,
            "topics_configurations": {
                KAFKA_SERVICE_CONFIG_MAPPING[KafkaServices.payments][WEB_PAGE_CRAWLER]["topics"][0]: {
                    "tasks": [crawler]
                }
            },
            "async_kafka": False,
        },
        "docs_rag_indexer": {
            "service_name": KafkaServices.payments,
            "deserialization_format": KAFKA_SERIALIZATION_FORMAT,
            "consumer_config": COMMON_CONSUMER_CONFIG,
            "topics_configurations": {
                KAFKA_SERVICE_CONFIG_MAPPING[KafkaServices.payments][WEB_PAGE_INDEXER]["topics"][0]: {
                    "tasks": [indexer]
                }
            },
            "async_kafka": False,
        }

    }
}

KAFKA_CONSUMER_SETTINGS.update(KAFKA_CONSUMER_CONFIG)
