-- source_site + knowledge knowledge_base (MySQL 8 / compatible)
-- Soft delete via deleted_at; list APIs must filter deleted_at IS NULL.

CREATE TABLE IF NOT EXISTS knowledge_base (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    name            VARCHAR(128)  NOT NULL,
    description     VARCHAR(512)  NULL,
    embedding_model VARCHAR(128)  NOT NULL,
    embedding_dim   INT           NOT NULL DEFAULT 2048,
    status          TINYINT       NOT NULL DEFAULT 1,
    created_at      DATETIME(6)   NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at      DATETIME(6)   NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                                  ON UPDATE CURRENT_TIMESTAMP(6)
);

CREATE TABLE IF NOT EXISTS source_site (
    site_id            VARCHAR(64)  PRIMARY KEY,
    kb_id              BIGINT       NOT NULL,
    name               VARCHAR(256) NOT NULL,
    region             VARCHAR(8)   NOT NULL,
    category           VARCHAR(32)  NOT NULL,
    entry_url          VARCHAR(1024) NULL,
    crawl_mode         VARCHAR(32)  NOT NULL,
    allowed_domains    JSON         NOT NULL,
    rate_limit_qps     DOUBLE       NULL,
    status             VARCHAR(32)  NOT NULL DEFAULT 'pending_url',
    notes              TEXT         NULL,
    last_probe_at      DATETIME(6)  NULL,
    last_probe_status  VARCHAR(64)  NULL,
    created_at         DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at         DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                                   ON UPDATE CURRENT_TIMESTAMP(6),
    deleted_at         DATETIME(6)  NULL,
    CONSTRAINT fk_source_site_kb
        FOREIGN KEY (kb_id) REFERENCES knowledge_base (id),
    INDEX ix_source_site_kb_status (kb_id, status),
    INDEX ix_source_site_kb_region (kb_id, region)
);
