-- =============================================================================
-- PostgreSQL 权限：应用账号仅可操作 CACCH AI 表（cacch_ai_*）
-- 由 DBA 在超级用户下执行；按实际应用角色名修改 app_role
-- 禁止对共享库中其他业务表进行增删改（及 DDL）
-- =============================================================================
-- 使用前请替换：
--   :app_role  → 应用连接角色（当前示例为 esb，建议后续改为独立角色 cacch_ai_app）
-- =============================================================================

BEGIN;

-- 建议：为 AI 平台单独建角色（若已存在可跳过）
-- CREATE ROLE cacch_ai_app LOGIN PASSWORD '***';

-- 以下以当前 .env 中的 esb 为例；生产建议改用专用角色并收回 esb 上多余权限
DO $$
DECLARE
    app_role NAME := 'esb';
BEGIN
    -- 取消该角色在 public 下的建表权限（防止 create_all / 手工 DDL 污染其他命名）
    EXECUTE format('REVOKE CREATE ON SCHEMA public FROM %I', app_role);

    -- 仅授予 AI 表 DML + 必要 USAGE
    EXECUTE format('GRANT USAGE ON SCHEMA public TO %I', app_role);

    EXECUTE format(
        'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE cacch_ai_knowledge_base TO %I',
        app_role
    );
    EXECUTE format(
        'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE cacch_ai_source_site TO %I',
        app_role
    );

    -- 序列（BIGSERIAL）
    EXECUTE format(
        'GRANT USAGE, SELECT ON SEQUENCE cacch_ai_knowledge_base_id_seq TO %I',
        app_role
    );

    -- 明确：不对其他表做 GRANT。若 esb 历史上拥有 ALL ON ALL TABLES，请 DBA 另行 REVOKE。
    RAISE NOTICE 'Granted DML on cacch_ai_* tables to role %', app_role;
END $$;

COMMIT;

-- ---------------------------------------------------------------------------
-- DBA 可选加固（按需手工执行，避免误伤其他业务）：
-- REVOKE ALL ON ALL TABLES IN SCHEMA public FROM esb;
-- 然后再执行本脚本中的 GRANT，仅恢复 cacch_ai_*。
-- ---------------------------------------------------------------------------
