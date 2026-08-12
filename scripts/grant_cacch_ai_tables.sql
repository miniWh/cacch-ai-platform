-- =============================================================================
-- PostgreSQL 权限：应用账号仅可操作 CACCH AI 表（cacch_ai_*）
-- 由 DBA 在超级用户下执行；按实际应用角色名修改 app_role
-- 禁止对共享库中其他业务表进行增删改（及 DDL）
-- =============================================================================
-- 使用前请替换：
--   app_role  → 应用连接角色（当前示例为 esb，建议后续改为独立角色 cacch_ai_app）
-- =============================================================================

BEGIN;

DO $$
DECLARE
    app_role NAME := 'esb';
    t TEXT;
BEGIN
    EXECUTE format('REVOKE CREATE ON SCHEMA public FROM %I', app_role);
    EXECUTE format('GRANT USAGE ON SCHEMA public TO %I', app_role);

    FOREACH t IN ARRAY ARRAY[
        'cacch_ai_knowledge_base',
        'cacch_ai_source_site',
        'cacch_ai_chat_session',
        'cacch_ai_chat_message',
        'cacch_ai_org',
        'cacch_ai_menu',
        'cacch_ai_role',
        'cacch_ai_role_menu',
        'cacch_ai_user',
        'cacch_ai_user_menu',
        'cacch_ai_auth_session',
        'cacch_ai_audit_log'
    ]
    LOOP
        EXECUTE format(
            'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE %I TO %I',
            t,
            app_role
        );
    END LOOP;

    -- BIGSERIAL 序列
    FOREACH t IN ARRAY ARRAY[
        'cacch_ai_knowledge_base_id_seq',
        'cacch_ai_org_id_seq',
        'cacch_ai_role_id_seq',
        'cacch_ai_user_id_seq',
        'cacch_ai_auth_session_id_seq',
        'cacch_ai_audit_log_id_seq'
    ]
    LOOP
        BEGIN
            EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %I TO %I', t, app_role);
        EXCEPTION
            WHEN undefined_table THEN
                RAISE NOTICE 'sequence % not found, skip', t;
        END;
    END LOOP;

    -- HR 主数据只读（开户/登录校验）；表名按实际库为准
    BEGIN
        EXECUTE format('GRANT SELECT ON TABLE persondetail TO %I', app_role);
    EXCEPTION
        WHEN undefined_table THEN
            RAISE NOTICE 'persondetail not found — grant SELECT manually when available';
    END;

    RAISE NOTICE 'Granted DML on cacch_ai_* (and SELECT persondetail if present) to role %', app_role;
END $$;

COMMIT;

-- ---------------------------------------------------------------------------
-- DBA 可选加固（按需手工执行，避免误伤其他业务）：
-- REVOKE ALL ON ALL TABLES IN SCHEMA public FROM esb;
-- 然后再执行本脚本中的 GRANT，仅恢复 cacch_ai_* + persondetail SELECT。
-- ---------------------------------------------------------------------------
