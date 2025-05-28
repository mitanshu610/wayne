PR_EVENT_EMITTER = 'pr_event_emitter'
PR_COMMENT_GENERATOR = 'pr_comment_generator'
WEB_PAGE_CRAWLER = 'web_page_crawler'
WEB_PAGE_INDEXER = 'web_page_indexer'

class KafkaServices:
    payments = "payments"


FEX_PAYMENTS_GROUP_ID = "fex-payments-group-id"

KAFKA_SERVICE_CONFIG_MAPPING = {
    KafkaServices.payments: {
        PR_EVENT_EMITTER: {
            "topics": ["azure-pr-event-emitter"],
            "group_id": FEX_PAYMENTS_GROUP_ID,
        },
        PR_COMMENT_GENERATOR: {
            "topics": ["azure-pr-comment-generator"],
            "group_id": FEX_PAYMENTS_GROUP_ID,
        },
        WEB_PAGE_CRAWLER: {
            "topics": ["fynd-json-docs-rag-crawler"],
            "group_id": FEX_PAYMENTS_GROUP_ID,
        },
        WEB_PAGE_INDEXER: {
            "topics": ["fynd-json-docs-rag-indexer"],
            "group_id": FEX_PAYMENTS_GROUP_ID,
        }
    }
}
