-- =============================================================================
-- PostgreSQL schema（AI 平台专用表，前缀 cacch_ai_）
-- 对齐 ORM：app/dao/models/knowledge_base.py、source_site.py
-- 约定：共享库 cdb 中仅允许本脚本维护 cacch_ai_* 表；禁止改动其他业务表
-- 软删除：cacch_ai_source_site.deleted_at；列表查询须过滤 deleted_at IS NULL
-- =============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 公共：updated_at 自动刷新（函数名带前缀，降低与库内其他对象冲突）
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION cacch_ai_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cacch_ai_set_updated_at() IS 'CACCH AI：BEFORE UPDATE 触发器，自动刷新 updated_at';

-- ---------------------------------------------------------------------------
-- 知识库  cacch_ai_knowledge_base
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cacch_ai_knowledge_base (
    id              BIGSERIAL PRIMARY KEY,
    name            VARCHAR(128)  NOT NULL,
    description     VARCHAR(512)  NULL,
    embedding_model VARCHAR(128)  NOT NULL,
    embedding_dim   INTEGER       NOT NULL DEFAULT 2048,
    status          SMALLINT      NOT NULL DEFAULT 1,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE  cacch_ai_knowledge_base IS '【CACCH AI】知识库：RAG 检索与文档/站点资源的归属单元';
COMMENT ON COLUMN cacch_ai_knowledge_base.id IS '知识库主键 ID';
COMMENT ON COLUMN cacch_ai_knowledge_base.name IS '知识库名称';
COMMENT ON COLUMN cacch_ai_knowledge_base.description IS '知识库描述';
COMMENT ON COLUMN cacch_ai_knowledge_base.embedding_model IS '绑定的 Embedding 模型名（维度变更需重建向量）';
COMMENT ON COLUMN cacch_ai_knowledge_base.embedding_dim IS '向量维度，须与 Embedding 模型输出一致';
COMMENT ON COLUMN cacch_ai_knowledge_base.status IS '状态：1=启用，0=停用';
COMMENT ON COLUMN cacch_ai_knowledge_base.created_at IS '创建时间';
COMMENT ON COLUMN cacch_ai_knowledge_base.updated_at IS '最后更新时间';

DROP TRIGGER IF EXISTS trg_cacch_ai_knowledge_base_updated_at ON cacch_ai_knowledge_base;
CREATE TRIGGER trg_cacch_ai_knowledge_base_updated_at
    BEFORE UPDATE ON cacch_ai_knowledge_base
    FOR EACH ROW
    EXECUTE PROCEDURE cacch_ai_set_updated_at();

-- ---------------------------------------------------------------------------
-- 站点清单  cacch_ai_source_site
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cacch_ai_source_site (
    site_id            VARCHAR(64)   PRIMARY KEY,
    kb_id              BIGINT        NOT NULL,
    name               VARCHAR(256)  NOT NULL,
    region             VARCHAR(8)    NOT NULL,
    category           VARCHAR(32)   NOT NULL,
    entry_url          VARCHAR(1024) NULL,
    crawl_mode         VARCHAR(32)   NOT NULL,
    allowed_domains    JSONB         NOT NULL DEFAULT '[]'::jsonb,
    rate_limit_qps     DOUBLE PRECISION NULL,
    status             VARCHAR(32)   NOT NULL DEFAULT 'pending_url',
    notes              TEXT          NULL,
    last_probe_at      TIMESTAMPTZ   NULL,
    last_probe_status  VARCHAR(64)   NULL,
    created_at         TIMESTAMPTZ   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMPTZ   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at         TIMESTAMPTZ   NULL,
    CONSTRAINT fk_cacch_ai_source_site_kb
        FOREIGN KEY (kb_id) REFERENCES cacch_ai_knowledge_base (id)
);

COMMENT ON TABLE  cacch_ai_source_site IS '【CACCH AI】站点清单：资料查询网站目录，仅页面维护，归属指定知识库';
COMMENT ON COLUMN cacch_ai_source_site.site_id IS '站点稳定主键，如 us_ppis、eu_efsa_publications';
COMMENT ON COLUMN cacch_ai_source_site.kb_id IS '所属知识库 ID，关联 cacch_ai_knowledge_base.id';
COMMENT ON COLUMN cacch_ai_source_site.name IS '站点展示名称';
COMMENT ON COLUMN cacch_ai_source_site.region IS '地区代码：US/EU/UK/AU/JP/CN/INT 等';
COMMENT ON COLUMN cacch_ai_source_site.category IS '类别：registration=登记，evaluation=评审，standard=标准，database=数据库';
COMMENT ON COLUMN cacch_ai_source_site.entry_url IS '入口 URL；为空时 status 通常为 pending_url';
COMMENT ON COLUMN cacch_ai_source_site.crawl_mode IS '采集模式：manual / single_page / list_harvest / connector';
COMMENT ON COLUMN cacch_ai_source_site.allowed_domains IS '出站域名白名单 JSON 数组，如 ["efsa.europa.eu"]';
COMMENT ON COLUMN cacch_ai_source_site.rate_limit_qps IS '站点限速（QPS 或间隔策略数值），可空';
COMMENT ON COLUMN cacch_ai_source_site.status IS '状态：active / broken / pending_url / disabled';
COMMENT ON COLUMN cacch_ai_source_site.notes IS '备注（笔误、需日文名、合规说明等）';
COMMENT ON COLUMN cacch_ai_source_site.last_probe_at IS '最近一次链接探活时间';
COMMENT ON COLUMN cacch_ai_source_site.last_probe_status IS '最近探活结果（HTTP 状态码或错误摘要）';
COMMENT ON COLUMN cacch_ai_source_site.created_at IS '创建时间';
COMMENT ON COLUMN cacch_ai_source_site.updated_at IS '最后更新时间';
COMMENT ON COLUMN cacch_ai_source_site.deleted_at IS '软删除时间；非空表示已删除，列表须过滤';

CREATE INDEX IF NOT EXISTS ix_cacch_ai_source_site_kb_id
    ON cacch_ai_source_site (kb_id);

CREATE INDEX IF NOT EXISTS ix_cacch_ai_source_site_kb_status
    ON cacch_ai_source_site (kb_id, status);

CREATE INDEX IF NOT EXISTS ix_cacch_ai_source_site_kb_region
    ON cacch_ai_source_site (kb_id, region);

CREATE INDEX IF NOT EXISTS ix_cacch_ai_source_site_alive
    ON cacch_ai_source_site (deleted_at)
    WHERE deleted_at IS NULL;

DROP TRIGGER IF EXISTS trg_cacch_ai_source_site_updated_at ON cacch_ai_source_site;
CREATE TRIGGER trg_cacch_ai_source_site_updated_at
    BEFORE UPDATE ON cacch_ai_source_site
    FOR EACH ROW
    EXECUTE PROCEDURE cacch_ai_set_updated_at();

COMMIT;
