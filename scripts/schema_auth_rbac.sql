-- =============================================================================
-- PostgreSQL：工作台登录 / 组织树 / 角色菜单权限（cacch_ai_*）
-- 对齐需求：docs/platform/07-工作台登录组织与菜单权限需求.md
-- 由运维/开发手动执行；仅操作 cacch_ai_*；禁止 DDL/DML 改写 persondetail
-- 依赖：cacch_ai_set_updated_at()（见 scripts/schema_source_site.sql）
-- HR 只读：开户/登录时 SELECT persondetail（mobileNo/staffNo/staffName/workEmail/staffStatus）
-- =============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 1. 组织树  cacch_ai_org
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cacch_ai_org (
    id              BIGSERIAL PRIMARY KEY,
    parent_id       BIGINT        NULL,
    code            VARCHAR(64)   NULL,
    name            VARCHAR(128)  NOT NULL,
    sort_order      INTEGER       NOT NULL DEFAULT 0,
    status          VARCHAR(16)   NOT NULL DEFAULT 'active',
    remark          VARCHAR(512)  NULL,
    created_at      TIMESTAMP     NOT NULL DEFAULT LOCALTIMESTAMP,
    updated_at      TIMESTAMP     NOT NULL DEFAULT LOCALTIMESTAMP,
    CONSTRAINT fk_cacch_ai_org_parent
        FOREIGN KEY (parent_id) REFERENCES cacch_ai_org (id),
    CONSTRAINT ck_cacch_ai_org_status
        CHECK (status IN ('active', 'disabled'))
);

COMMENT ON TABLE  cacch_ai_org IS '【CACCH AI】组织树：账号必须挂靠某一节点';
COMMENT ON COLUMN cacch_ai_org.id IS '组织节点主键';
COMMENT ON COLUMN cacch_ai_org.parent_id IS '父节点；根节点为空';
COMMENT ON COLUMN cacch_ai_org.code IS '组织编码，可选唯一业务码';
COMMENT ON COLUMN cacch_ai_org.name IS '组织名称';
COMMENT ON COLUMN cacch_ai_org.sort_order IS '同级排序，越小越靠前';
COMMENT ON COLUMN cacch_ai_org.status IS 'active=启用；disabled=停用（停用后禁止新挂靠，且该节点下账号禁止登录）';
COMMENT ON COLUMN cacch_ai_org.remark IS '备注';
COMMENT ON COLUMN cacch_ai_org.created_at IS '创建时间（Asia/Shanghai 墙钟）';
COMMENT ON COLUMN cacch_ai_org.updated_at IS '更新时间（Asia/Shanghai 墙钟）';

CREATE UNIQUE INDEX IF NOT EXISTS uq_cacch_ai_org_code
    ON cacch_ai_org (code)
    WHERE code IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_cacch_ai_org_parent_sort
    ON cacch_ai_org (parent_id, sort_order);

DROP TRIGGER IF EXISTS trg_cacch_ai_org_updated_at ON cacch_ai_org;
CREATE TRIGGER trg_cacch_ai_org_updated_at
    BEFORE UPDATE ON cacch_ai_org
    FOR EACH ROW
    EXECUTE PROCEDURE cacch_ai_set_updated_at();

-- ---------------------------------------------------------------------------
-- 2. 系统菜单  cacch_ai_menu（权限粒度仅到菜单）
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cacch_ai_menu (
    id              VARCHAR(64)   PRIMARY KEY,
    title           VARCHAR(64)   NOT NULL,
    path            VARCHAR(128)  NOT NULL,
    icon            VARCHAR(32)   NULL,
    sort_order      INTEGER       NOT NULL DEFAULT 0,
    assignable      BOOLEAN       NOT NULL DEFAULT TRUE,
    status          VARCHAR(16)   NOT NULL DEFAULT 'active',
    remark          VARCHAR(256)  NULL,
    created_at      TIMESTAMP     NOT NULL DEFAULT LOCALTIMESTAMP,
    updated_at      TIMESTAMP     NOT NULL DEFAULT LOCALTIMESTAMP,
    CONSTRAINT ck_cacch_ai_menu_status
        CHECK (status IN ('active', 'disabled'))
);

COMMENT ON TABLE  cacch_ai_menu IS '【CACCH AI】系统菜单目录；授权仅到菜单级';
COMMENT ON COLUMN cacch_ai_menu.id IS '菜单稳定 ID，如 chat / sites / users';
COMMENT ON COLUMN cacch_ai_menu.title IS '侧栏展示名称';
COMMENT ON COLUMN cacch_ai_menu.path IS '前端路由 path';
COMMENT ON COLUMN cacch_ai_menu.icon IS '图标名（与前端约定）';
COMMENT ON COLUMN cacch_ai_menu.sort_order IS '排序，越小越靠前';
COMMENT ON COLUMN cacch_ai_menu.assignable IS '是否允许授权给普通角色/账号；false=仅种子超管策略使用';
COMMENT ON COLUMN cacch_ai_menu.status IS 'active / disabled';
COMMENT ON COLUMN cacch_ai_menu.remark IS '备注';

CREATE UNIQUE INDEX IF NOT EXISTS uq_cacch_ai_menu_path
    ON cacch_ai_menu (path);

DROP TRIGGER IF EXISTS trg_cacch_ai_menu_updated_at ON cacch_ai_menu;
CREATE TRIGGER trg_cacch_ai_menu_updated_at
    BEFORE UPDATE ON cacch_ai_menu
    FOR EACH ROW
    EXECUTE PROCEDURE cacch_ai_set_updated_at();

-- ---------------------------------------------------------------------------
-- 3. 角色模板  cacch_ai_role
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cacch_ai_role (
    id              BIGSERIAL PRIMARY KEY,
    code            VARCHAR(64)   NOT NULL,
    name            VARCHAR(64)   NOT NULL,
    description     VARCHAR(256)  NULL,
    is_system       BOOLEAN       NOT NULL DEFAULT FALSE,
    status          VARCHAR(16)   NOT NULL DEFAULT 'active',
    created_at      TIMESTAMP     NOT NULL DEFAULT LOCALTIMESTAMP,
    updated_at      TIMESTAMP     NOT NULL DEFAULT LOCALTIMESTAMP,
    CONSTRAINT uq_cacch_ai_role_code UNIQUE (code),
    CONSTRAINT ck_cacch_ai_role_status
        CHECK (status IN ('active', 'disabled'))
);

COMMENT ON TABLE  cacch_ai_role IS '【CACCH AI】角色模板：绑定默认菜单集，开户可套用后再微调';
COMMENT ON COLUMN cacch_ai_role.code IS '角色编码，如 user / ops / admin';
COMMENT ON COLUMN cacch_ai_role.name IS '角色显示名';
COMMENT ON COLUMN cacch_ai_role.is_system IS '系统预置角色（限制删除）';
COMMENT ON COLUMN cacch_ai_role.status IS 'active / disabled';

DROP TRIGGER IF EXISTS trg_cacch_ai_role_updated_at ON cacch_ai_role;
CREATE TRIGGER trg_cacch_ai_role_updated_at
    BEFORE UPDATE ON cacch_ai_role
    FOR EACH ROW
    EXECUTE PROCEDURE cacch_ai_set_updated_at();

-- ---------------------------------------------------------------------------
-- 4. 角色默认菜单  cacch_ai_role_menu
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cacch_ai_role_menu (
    role_id         BIGINT        NOT NULL,
    menu_id         VARCHAR(64)   NOT NULL,
    created_at      TIMESTAMP     NOT NULL DEFAULT LOCALTIMESTAMP,
    PRIMARY KEY (role_id, menu_id),
    CONSTRAINT fk_cacch_ai_role_menu_role
        FOREIGN KEY (role_id) REFERENCES cacch_ai_role (id) ON DELETE CASCADE,
    CONSTRAINT fk_cacch_ai_role_menu_menu
        FOREIGN KEY (menu_id) REFERENCES cacch_ai_menu (id) ON DELETE CASCADE
);

COMMENT ON TABLE cacch_ai_role_menu IS '【CACCH AI】角色模板默认菜单；修改默认集不强制回溯已有账号';

CREATE INDEX IF NOT EXISTS ix_cacch_ai_role_menu_menu
    ON cacch_ai_role_menu (menu_id);

-- ---------------------------------------------------------------------------
-- 5. 平台账号  cacch_ai_user
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cacch_ai_user (
    id                      BIGSERIAL PRIMARY KEY,
    staff_no                VARCHAR(64)   NOT NULL,
    mobile                  VARCHAR(32)   NOT NULL,
    name                    VARCHAR(128)  NOT NULL,
    email                   VARCHAR(256)  NULL,
    staff_status            VARCHAR(32)   NOT NULL,
    org_id                  BIGINT        NOT NULL,
    role_id                 BIGINT        NULL,
    password_hash           VARCHAR(255)  NOT NULL,
    must_change_password    BOOLEAN       NOT NULL DEFAULT TRUE,
    status                  VARCHAR(16)   NOT NULL DEFAULT 'active',
    token_version           INTEGER       NOT NULL DEFAULT 0,
    failed_login_count      INTEGER       NOT NULL DEFAULT 0,
    locked_until            TIMESTAMP     NULL,
    last_login_at           TIMESTAMP     NULL,
    password_changed_at     TIMESTAMP     NULL,
    created_by              BIGINT        NULL,
    remark                  VARCHAR(512)  NULL,
    created_at              TIMESTAMP     NOT NULL DEFAULT LOCALTIMESTAMP,
    updated_at              TIMESTAMP     NOT NULL DEFAULT LOCALTIMESTAMP,
    CONSTRAINT uq_cacch_ai_user_staff_no UNIQUE (staff_no),
    CONSTRAINT uq_cacch_ai_user_mobile UNIQUE (mobile),
    CONSTRAINT fk_cacch_ai_user_org
        FOREIGN KEY (org_id) REFERENCES cacch_ai_org (id),
    CONSTRAINT fk_cacch_ai_user_role
        FOREIGN KEY (role_id) REFERENCES cacch_ai_role (id),
    CONSTRAINT fk_cacch_ai_user_created_by
        FOREIGN KEY (created_by) REFERENCES cacch_ai_user (id),
    CONSTRAINT ck_cacch_ai_user_status
        CHECK (status IN ('active', 'disabled'))
);

COMMENT ON TABLE  cacch_ai_user IS '【CACCH AI】工作台账号；禁止自助注册，仅管理员开户；须挂组织';
COMMENT ON COLUMN cacch_ai_user.staff_no IS '用户 ID=persondetail.staffNo=企微 UserId，后续 SSO 主键';
COMMENT ON COLUMN cacch_ai_user.mobile IS '登录手机号=persondetail.mobileNo（可含国际号）；唯一';
COMMENT ON COLUMN cacch_ai_user.name IS '姓名=开户时 persondetail.staffName';
COMMENT ON COLUMN cacch_ai_user.email IS '邮箱=开户时 persondetail.workEmail';
COMMENT ON COLUMN cacch_ai_user.staff_status IS '开户时写入的 HR 在职状态；IN_SERVICE=在职';
COMMENT ON COLUMN cacch_ai_user.org_id IS '所属组织节点（必填，单组织）';
COMMENT ON COLUMN cacch_ai_user.role_id IS '开户/调整时选用的角色模板（可空）；有效菜单以 user_menu 为准';
COMMENT ON COLUMN cacch_ai_user.password_hash IS '密码哈希，禁止存明文';
COMMENT ON COLUMN cacch_ai_user.must_change_password IS 'true=须先改密才能进业务';
COMMENT ON COLUMN cacch_ai_user.status IS 'active / disabled；停用后不可登录且 Token 失效';
COMMENT ON COLUMN cacch_ai_user.token_version IS '令牌版本；改密/停用/登出全会话时递增，使旧 Token 失效';
COMMENT ON COLUMN cacch_ai_user.failed_login_count IS '连续登录失败次数，成功登录清零';
COMMENT ON COLUMN cacch_ai_user.locked_until IS '锁定截止时间（墙钟）；未到点拒绝登录';
COMMENT ON COLUMN cacch_ai_user.last_login_at IS '最近登录成功时间';
COMMENT ON COLUMN cacch_ai_user.password_changed_at IS '最近改密时间';
COMMENT ON COLUMN cacch_ai_user.created_by IS '开户管理员用户主键';
COMMENT ON COLUMN cacch_ai_user.remark IS '管理员备注';

CREATE INDEX IF NOT EXISTS ix_cacch_ai_user_org_id
    ON cacch_ai_user (org_id);

CREATE INDEX IF NOT EXISTS ix_cacch_ai_user_role_id
    ON cacch_ai_user (role_id);

CREATE INDEX IF NOT EXISTS ix_cacch_ai_user_status
    ON cacch_ai_user (status);

DROP TRIGGER IF EXISTS trg_cacch_ai_user_updated_at ON cacch_ai_user;
CREATE TRIGGER trg_cacch_ai_user_updated_at
    BEFORE UPDATE ON cacch_ai_user
    FOR EACH ROW
    EXECUTE PROCEDURE cacch_ai_set_updated_at();

-- ---------------------------------------------------------------------------
-- 6. 账号有效菜单  cacch_ai_user_menu（最终授权；可自角色模板复制后微调）
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cacch_ai_user_menu (
    user_id         BIGINT        NOT NULL,
    menu_id         VARCHAR(64)   NOT NULL,
    created_at      TIMESTAMP     NOT NULL DEFAULT LOCALTIMESTAMP,
    PRIMARY KEY (user_id, menu_id),
    CONSTRAINT fk_cacch_ai_user_menu_user
        FOREIGN KEY (user_id) REFERENCES cacch_ai_user (id) ON DELETE CASCADE,
    CONSTRAINT fk_cacch_ai_user_menu_menu
        FOREIGN KEY (menu_id) REFERENCES cacch_ai_menu (id) ON DELETE CASCADE
);

COMMENT ON TABLE cacch_ai_user_menu IS '【CACCH AI】账号有效菜单权限（侧栏与路由以本表为准）';

CREATE INDEX IF NOT EXISTS ix_cacch_ai_user_menu_menu
    ON cacch_ai_user_menu (menu_id);

-- ---------------------------------------------------------------------------
-- 7. 登录会话 / 今日免登录  cacch_ai_auth_session
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cacch_ai_auth_session (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             BIGINT        NOT NULL,
    refresh_token_hash  VARCHAR(128)  NOT NULL,
    token_version       INTEGER       NOT NULL,
    remember_today      BOOLEAN       NOT NULL DEFAULT FALSE,
    expires_at          TIMESTAMP     NOT NULL,
    revoked_at          TIMESTAMP     NULL,
    user_agent          VARCHAR(512)  NULL,
    client_ip           VARCHAR(64)   NULL,
    created_at          TIMESTAMP     NOT NULL DEFAULT LOCALTIMESTAMP,
    CONSTRAINT uq_cacch_ai_auth_session_refresh UNIQUE (refresh_token_hash),
    CONSTRAINT fk_cacch_ai_auth_session_user
        FOREIGN KEY (user_id) REFERENCES cacch_ai_user (id) ON DELETE CASCADE
);

COMMENT ON TABLE  cacch_ai_auth_session IS '【CACCH AI】登录会话；支持今日免登录与主动吊销';
COMMENT ON COLUMN cacch_ai_auth_session.refresh_token_hash IS '刷新令牌哈希（不明文存储）';
COMMENT ON COLUMN cacch_ai_auth_session.token_version IS '签发时用户 token_version 快照；不一致则视为失效';
COMMENT ON COLUMN cacch_ai_auth_session.remember_today IS 'true=今日免登录（建议 expires_at=当日 23:59:59 Asia/Shanghai）';
COMMENT ON COLUMN cacch_ai_auth_session.expires_at IS '会话过期时间（墙钟）';
COMMENT ON COLUMN cacch_ai_auth_session.revoked_at IS '登出/强制失效时间；非空表示已吊销';

CREATE INDEX IF NOT EXISTS ix_cacch_ai_auth_session_user_alive
    ON cacch_ai_auth_session (user_id, expires_at)
    WHERE revoked_at IS NULL;

-- ---------------------------------------------------------------------------
-- 8. 审计日志  cacch_ai_audit_log
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cacch_ai_audit_log (
    id              BIGSERIAL PRIMARY KEY,
    actor_user_id   BIGINT        NULL,
    actor_staff_no  VARCHAR(64)   NULL,
    action          VARCHAR(64)   NOT NULL,
    target_type     VARCHAR(64)   NULL,
    target_id       VARCHAR(64)   NULL,
    success         BOOLEAN       NOT NULL DEFAULT TRUE,
    detail_json     JSONB         NULL,
    client_ip       VARCHAR(64)   NULL,
    created_at      TIMESTAMP     NOT NULL DEFAULT LOCALTIMESTAMP
);

COMMENT ON TABLE  cacch_ai_audit_log IS '【CACCH AI】安全审计：登录成败、开户、重置密码、改密、授权、启停等';
COMMENT ON COLUMN cacch_ai_audit_log.actor_user_id IS '操作者用户主键；系统/匿名可空';
COMMENT ON COLUMN cacch_ai_audit_log.actor_staff_no IS '操作者 staff_no 冗余，便于检索';
COMMENT ON COLUMN cacch_ai_audit_log.action IS '动作码，如 login_ok / login_fail / user_create / password_reset / menu_grant';
COMMENT ON COLUMN cacch_ai_audit_log.target_type IS '对象类型：user / org / role / session 等';
COMMENT ON COLUMN cacch_ai_audit_log.target_id IS '对象 ID 字符串';
COMMENT ON COLUMN cacch_ai_audit_log.success IS '是否成功';
COMMENT ON COLUMN cacch_ai_audit_log.detail_json IS '附加详情（禁止写入明文密码）';

CREATE INDEX IF NOT EXISTS ix_cacch_ai_audit_log_created
    ON cacch_ai_audit_log (created_at DESC);

CREATE INDEX IF NOT EXISTS ix_cacch_ai_audit_log_action_created
    ON cacch_ai_audit_log (action, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_cacch_ai_audit_log_actor
    ON cacch_ai_audit_log (actor_user_id, created_at DESC);

-- ---------------------------------------------------------------------------
-- 9. 种子数据：菜单 / 角色模板 / 根组织
-- ---------------------------------------------------------------------------
INSERT INTO cacch_ai_menu (id, title, path, icon, sort_order, assignable, status)
VALUES
    ('chat',      '对话台',     '/chat',      'chat',     10, TRUE,  'active'),
    ('sites',     '站点清单',   '/sites',     'list',     20, TRUE,  'active'),
    ('documents', '文档与任务', '/documents', 'document', 30, TRUE,  'active'),
    ('settings',  '应用配置',   '/settings',  'setting',  40, TRUE,  'active'),
    ('menus',     '菜单管理',   '/menus',     'menu',     50, TRUE,  'active'),
    ('orgs',      '组织管理',   '/orgs',      'menu',     60, TRUE,  'active'),
    ('roles',     '角色管理',   '/roles',     'menu',     70, TRUE,  'active'),
    ('users',     '账号管理',   '/users',     'menu',     80, TRUE,  'active')
ON CONFLICT (id) DO UPDATE
SET title = EXCLUDED.title,
    path = EXCLUDED.path,
    icon = EXCLUDED.icon,
    sort_order = EXCLUDED.sort_order,
    assignable = EXCLUDED.assignable,
    status = EXCLUDED.status,
    updated_at = LOCALTIMESTAMP;

INSERT INTO cacch_ai_role (code, name, description, is_system, status)
VALUES
    ('user',  '普通用户', '默认可访问对话台', TRUE, 'active'),
    ('ops',   '运维',     '对话台 + 站点/文档等运维菜单', TRUE, 'active'),
    ('admin', '管理员',   '含组织/角色/账号等管理菜单', TRUE, 'active')
ON CONFLICT (code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    is_system = EXCLUDED.is_system,
    status = EXCLUDED.status,
    updated_at = LOCALTIMESTAMP;

-- 角色默认菜单（按 code 解析 id，可重复执行）
INSERT INTO cacch_ai_role_menu (role_id, menu_id)
SELECT r.id, v.menu_id
FROM (
    VALUES
        ('user', 'chat'),
        ('ops', 'chat'),
        ('ops', 'sites'),
        ('ops', 'documents'),
        ('ops', 'settings'),
        ('admin', 'chat'),
        ('admin', 'sites'),
        ('admin', 'documents'),
        ('admin', 'settings'),
        ('admin', 'menus'),
        ('admin', 'orgs'),
        ('admin', 'roles'),
        ('admin', 'users')
) AS v(role_code, menu_id)
JOIN cacch_ai_role r ON r.code = v.role_code
ON CONFLICT DO NOTHING;

INSERT INTO cacch_ai_org (parent_id, code, name, sort_order, status, remark)
SELECT NULL, 'ROOT', '根组织', 0, 'active', '默认根节点；可在此下建部门'
WHERE NOT EXISTS (SELECT 1 FROM cacch_ai_org WHERE code = 'ROOT');

COMMIT;

-- =============================================================================
-- DBA 补充（勿写入本事务自动执行，按环境执行）：
-- 1) 应用角色需对本脚本新建表 GRANT DML（见 scripts/grant_cacch_ai_tables.sql）
-- 2) 只读 HR：GRANT SELECT ON TABLE persondetail TO <app_role>;
-- 3) 首个管理员账号由应用开户流程写入（需已存在 IN_SERVICE 的 persondetail 手机号），
--    或运维在验证环境后手工 INSERT（password_hash 须为应用约定算法）
-- =============================================================================
