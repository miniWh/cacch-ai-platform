-- =============================================================================
-- PostgreSQL：对话会话 / 消息（cacch_ai_chat_session / cacch_ai_chat_message）
-- 由运维/开发手动执行；仅操作 cacch_ai_* 表，不改库级时区或其他业务表
-- 依赖：cacch_ai_knowledge_base 已存在；cacch_ai_set_updated_at() 已存在（见 schema_source_site.sql）
-- =============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 会话  cacch_ai_chat_session
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cacch_ai_chat_session (
    session_id      VARCHAR(64)   PRIMARY KEY,
    kb_id           BIGINT        NOT NULL,
    app_id          BIGINT        NULL,
    user_id         VARCHAR(64)   NULL,
    title           VARCHAR(128)  NOT NULL DEFAULT '新对话',
    title_locked    BOOLEAN       NOT NULL DEFAULT FALSE,
    pinned          BOOLEAN       NOT NULL DEFAULT FALSE,
    pinned_at       TIMESTAMP     NULL,
    created_at      TIMESTAMP     NOT NULL DEFAULT LOCALTIMESTAMP,
    updated_at      TIMESTAMP     NOT NULL DEFAULT LOCALTIMESTAMP,
    deleted_at      TIMESTAMP     NULL,
    CONSTRAINT fk_cacch_ai_chat_session_kb
        FOREIGN KEY (kb_id) REFERENCES cacch_ai_knowledge_base (id)
);

COMMENT ON TABLE  cacch_ai_chat_session IS '【CACCH AI】对话会话：对话台会话列表，支持置顶/重命名/软删';
COMMENT ON COLUMN cacch_ai_chat_session.session_id IS '会话主键，如 s_1710000000000';
COMMENT ON COLUMN cacch_ai_chat_session.kb_id IS '绑定知识库 ID';
COMMENT ON COLUMN cacch_ai_chat_session.app_id IS '平台 App ID，可选';
COMMENT ON COLUMN cacch_ai_chat_session.user_id IS '用户标识，预留隔离';
COMMENT ON COLUMN cacch_ai_chat_session.title IS '会话标题';
COMMENT ON COLUMN cacch_ai_chat_session.title_locked IS 'true=用户已重命名，禁止自动用首条消息覆盖标题';
COMMENT ON COLUMN cacch_ai_chat_session.pinned IS '是否置顶';
COMMENT ON COLUMN cacch_ai_chat_session.pinned_at IS '置顶时间（Asia/Shanghai 墙钟）；取消置顶置空';
COMMENT ON COLUMN cacch_ai_chat_session.created_at IS '创建时间（Asia/Shanghai 墙钟）';
COMMENT ON COLUMN cacch_ai_chat_session.updated_at IS '最后活跃时间（Asia/Shanghai 墙钟）';
COMMENT ON COLUMN cacch_ai_chat_session.deleted_at IS '软删除时间；非空表示已删除';

CREATE INDEX IF NOT EXISTS ix_cacch_ai_chat_session_kb_alive
    ON cacch_ai_chat_session (kb_id, pinned DESC, pinned_at DESC NULLS LAST, updated_at DESC)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS ix_cacch_ai_chat_session_kb_id
    ON cacch_ai_chat_session (kb_id);

DROP TRIGGER IF EXISTS trg_cacch_ai_chat_session_updated_at ON cacch_ai_chat_session;
CREATE TRIGGER trg_cacch_ai_chat_session_updated_at
    BEFORE UPDATE ON cacch_ai_chat_session
    FOR EACH ROW
    EXECUTE PROCEDURE cacch_ai_set_updated_at();

-- ---------------------------------------------------------------------------
-- 消息  cacch_ai_chat_message
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cacch_ai_chat_message (
    message_id      VARCHAR(64)   PRIMARY KEY,
    session_id      VARCHAR(64)   NOT NULL,
    role            VARCHAR(16)   NOT NULL,
    content         TEXT          NOT NULL,
    citations_json  JSONB         NULL,
    created_at      TIMESTAMP     NOT NULL DEFAULT LOCALTIMESTAMP,
    CONSTRAINT fk_cacch_ai_chat_message_session
        FOREIGN KEY (session_id) REFERENCES cacch_ai_chat_session (session_id)
        ON DELETE CASCADE,
    CONSTRAINT ck_cacch_ai_chat_message_role
        CHECK (role IN ('user', 'assistant', 'system'))
);

COMMENT ON TABLE  cacch_ai_chat_message IS '【CACCH AI】对话消息：归属会话，按 created_at 顺序展示';
COMMENT ON COLUMN cacch_ai_chat_message.message_id IS '消息主键';
COMMENT ON COLUMN cacch_ai_chat_message.session_id IS '所属会话';
COMMENT ON COLUMN cacch_ai_chat_message.role IS 'user / assistant / system';
COMMENT ON COLUMN cacch_ai_chat_message.content IS '消息正文';
COMMENT ON COLUMN cacch_ai_chat_message.citations_json IS '引用来源 JSON 数组，可空';
COMMENT ON COLUMN cacch_ai_chat_message.created_at IS '创建时间（Asia/Shanghai 墙钟）';

CREATE INDEX IF NOT EXISTS ix_cacch_ai_chat_message_session_created
    ON cacch_ai_chat_message (session_id, created_at);

COMMIT;
