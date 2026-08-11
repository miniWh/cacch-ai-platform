-- =============================================================================
-- 将 cacch_ai_* 时间列从 TIMESTAMPTZ 改为 TIMESTAMP（无时区）
-- 存储 Asia/Shanghai 墙钟，IDE 任意会话时区下展示数字一致
-- 不修改数据库/角色默认 TimeZone，不影响其他业务表
-- =============================================================================

BEGIN;

-- 触发器：LOCALTIMESTAMP = 会话本地墙钟；应用连接已 SET Asia/Shanghai
CREATE OR REPLACE FUNCTION cacch_ai_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = LOCALTIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cacch_ai_set_updated_at() IS
    'CACCH AI：BEFORE UPDATE，刷新 updated_at（TIMESTAMP 墙钟，依赖会话 TimeZone=Asia/Shanghai）';

-- knowledge_base
ALTER TABLE cacch_ai_knowledge_base
    ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE
        USING (created_at AT TIME ZONE 'Asia/Shanghai'),
    ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE
        USING (updated_at AT TIME ZONE 'Asia/Shanghai'),
    ALTER COLUMN created_at SET DEFAULT LOCALTIMESTAMP,
    ALTER COLUMN updated_at SET DEFAULT LOCALTIMESTAMP;

COMMENT ON COLUMN cacch_ai_knowledge_base.created_at IS '创建时间（Asia/Shanghai 墙钟，无时区）';
COMMENT ON COLUMN cacch_ai_knowledge_base.updated_at IS '最后更新时间（Asia/Shanghai 墙钟，无时区）';

-- source_site
ALTER TABLE cacch_ai_source_site
    ALTER COLUMN last_probe_at TYPE TIMESTAMP WITHOUT TIME ZONE
        USING (
            CASE
                WHEN last_probe_at IS NULL THEN NULL
                ELSE last_probe_at AT TIME ZONE 'Asia/Shanghai'
            END
        ),
    ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE
        USING (created_at AT TIME ZONE 'Asia/Shanghai'),
    ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE
        USING (updated_at AT TIME ZONE 'Asia/Shanghai'),
    ALTER COLUMN deleted_at TYPE TIMESTAMP WITHOUT TIME ZONE
        USING (
            CASE
                WHEN deleted_at IS NULL THEN NULL
                ELSE deleted_at AT TIME ZONE 'Asia/Shanghai'
            END
        ),
    ALTER COLUMN created_at SET DEFAULT LOCALTIMESTAMP,
    ALTER COLUMN updated_at SET DEFAULT LOCALTIMESTAMP;

COMMENT ON COLUMN cacch_ai_source_site.last_probe_at IS '最近一次链接探活时间（Asia/Shanghai 墙钟）';
COMMENT ON COLUMN cacch_ai_source_site.created_at IS '创建时间（Asia/Shanghai 墙钟，无时区）';
COMMENT ON COLUMN cacch_ai_source_site.updated_at IS '最后更新时间（Asia/Shanghai 墙钟，无时区）';
COMMENT ON COLUMN cacch_ai_source_site.deleted_at IS '软删除时间（Asia/Shanghai 墙钟）；非空表示已删除';

COMMIT;
