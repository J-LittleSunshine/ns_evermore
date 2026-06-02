CREATE TABLE iam_company
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_code VARCHAR(64) NOT NULL,
    company_name VARCHAR(128) NOT NULL,
    legal_name VARCHAR(128) NULL,
    status INTEGER NOT NULL DEFAULT 1,
    created_by INTEGER NULL,
    updated_by INTEGER NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_comp_stat CHECK (status IN (0, 1))
);
CREATE UNIQUE INDEX uk_comp_code ON iam_company (company_code);
CREATE INDEX idx_comp_created_by ON iam_company (created_by);
CREATE INDEX idx_comp_updated_by ON iam_company (updated_by);

CREATE TABLE iam_subsidiary
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    subsidiary_code VARCHAR(64) NOT NULL,
    subsidiary_name VARCHAR(128) NOT NULL,
    status INTEGER NOT NULL DEFAULT 1,
    created_by INTEGER NULL,
    updated_by INTEGER NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sub_comp FOREIGN KEY (company_id) REFERENCES iam_company (id),
    CONSTRAINT chk_sub_stat CHECK (status IN (0, 1))
);
CREATE UNIQUE INDEX uk_sub_code ON iam_subsidiary (subsidiary_code);
CREATE INDEX idx_sub_comp_id ON iam_subsidiary (company_id);
CREATE INDEX idx_sub_created_by ON iam_subsidiary (created_by);
CREATE INDEX idx_sub_updated_by ON iam_subsidiary (updated_by);

CREATE TABLE iam_department
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    subsidiary_id INTEGER NULL,
    parent_id INTEGER NULL,
    department_code VARCHAR(64) NOT NULL,
    department_name VARCHAR(128) NOT NULL,
    status INTEGER NOT NULL DEFAULT 1,
    created_by INTEGER NULL,
    updated_by INTEGER NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_dept_comp FOREIGN KEY (company_id) REFERENCES iam_company (id),
    CONSTRAINT fk_dept_sub FOREIGN KEY (subsidiary_id) REFERENCES iam_subsidiary (id),
    CONSTRAINT fk_dept_par FOREIGN KEY (parent_id) REFERENCES iam_department (id),
    CONSTRAINT chk_dept_stat CHECK (status IN (0, 1))
);
CREATE UNIQUE INDEX uk_dept_code ON iam_department (department_code);
CREATE INDEX idx_dept_comp_id ON iam_department (company_id);
CREATE INDEX idx_dept_sub_id ON iam_department (subsidiary_id);
CREATE INDEX idx_dept_par_id ON iam_department (parent_id);
CREATE INDEX idx_dept_created_by ON iam_department (created_by);
CREATE INDEX idx_dept_updated_by ON iam_department (updated_by);

CREATE TABLE iam_user
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(64) NOT NULL,
    password VARCHAR(128) NOT NULL,
    email VARCHAR(128) NULL,
    phone VARCHAR(32) NULL,
    display_name VARCHAR(64) NULL,
    user_type VARCHAR(32) NOT NULL,
    company_id INTEGER NULL,
    subsidiary_id INTEGER NULL,
    department_id INTEGER NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    is_staff INTEGER NOT NULL DEFAULT 0,
    is_superuser INTEGER NOT NULL DEFAULT 0,
    last_login TEXT NULL,
    created_by INTEGER NULL,
    updated_by INTEGER NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_comp FOREIGN KEY (company_id) REFERENCES iam_company (id),
    CONSTRAINT fk_user_sub FOREIGN KEY (subsidiary_id) REFERENCES iam_subsidiary (id),
    CONSTRAINT fk_user_dept FOREIGN KEY (department_id) REFERENCES iam_department (id),
    CONSTRAINT chk_user_type CHECK (user_type IN ('PERSONAL', 'ENTERPRISE')),
    CONSTRAINT chk_user_act CHECK (is_active IN (0, 1)),
    CONSTRAINT chk_user_staff CHECK (is_staff IN (0, 1)),
    CONSTRAINT chk_user_super CHECK (is_superuser IN (0, 1))
);
CREATE UNIQUE INDEX uk_user_name ON iam_user (username);
CREATE UNIQUE INDEX uk_user_email ON iam_user (email);
CREATE UNIQUE INDEX uk_user_phone ON iam_user (phone);
CREATE INDEX idx_user_type ON iam_user (user_type);
CREATE INDEX idx_user_comp_id ON iam_user (company_id);
CREATE INDEX idx_user_sub_id ON iam_user (subsidiary_id);
CREATE INDEX idx_user_dept_id ON iam_user (department_id);
CREATE INDEX idx_user_created_by ON iam_user (created_by);
CREATE INDEX idx_user_updated_by ON iam_user (updated_by);

CREATE TABLE iam_permission
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    permission_code VARCHAR(128) NOT NULL,
    permission_name VARCHAR(128) NOT NULL,
    permission_type VARCHAR(32) NOT NULL,
    parent_id INTEGER NULL,
    status INTEGER NOT NULL DEFAULT 1,
    created_by INTEGER NULL,
    updated_by INTEGER NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_perm_par FOREIGN KEY (parent_id) REFERENCES iam_permission (id),
    CONSTRAINT chk_perm_type CHECK (permission_type IN ('MENU', 'ACTION', 'DATA')),
    CONSTRAINT chk_perm_stat CHECK (status IN (0, 1))
);
CREATE UNIQUE INDEX uk_perm_code ON iam_permission (permission_code);
CREATE INDEX idx_perm_par_id ON iam_permission (parent_id);
CREATE INDEX idx_perm_created_by ON iam_permission (created_by);
CREATE INDEX idx_perm_updated_by ON iam_permission (updated_by);

CREATE TABLE iam_role
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_code VARCHAR(64) NOT NULL,
    role_name VARCHAR(128) NOT NULL,
    role_scope VARCHAR(32) NOT NULL,
    company_id INTEGER NULL,
    role_scope_company_id INTEGER GENERATED ALWAYS AS (IFNULL(company_id, 0)) STORED,
    status INTEGER NOT NULL DEFAULT 1,
    created_by INTEGER NULL,
    updated_by INTEGER NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_role_comp FOREIGN KEY (company_id) REFERENCES iam_company (id),
    CONSTRAINT chk_role_scope CHECK (role_scope IN ('PERSONAL', 'ENTERPRISE')),
    CONSTRAINT chk_role_scope_company CHECK ( (role_scope = 'PERSONAL' AND company_id IS NULL) OR (role_scope = 'ENTERPRISE' AND company_id IS NOT NULL) ),
    CONSTRAINT chk_role_stat CHECK (status IN (0, 1))
);
CREATE UNIQUE INDEX uk_role_scope_company_code ON iam_role (role_scope, role_scope_company_id, role_code);
CREATE INDEX idx_role_scope ON iam_role (role_scope);
CREATE INDEX idx_role_company_id ON iam_role (company_id);
CREATE INDEX idx_role_created_by ON iam_role (created_by);
CREATE INDEX idx_role_updated_by ON iam_role (updated_by);

CREATE TABLE iam_role_permission
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    data_scope VARCHAR(32) NULL,
    granted_by INTEGER NULL,
    expired_at TEXT NULL,
    created_by INTEGER NULL,
    updated_by INTEGER NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_rp_role FOREIGN KEY (role_id) REFERENCES iam_role (id),
    CONSTRAINT fk_rp_perm FOREIGN KEY (permission_id) REFERENCES iam_permission (id),
    CONSTRAINT chk_rp_data_scope CHECK ( data_scope IS NULL OR data_scope IN ('SELF', 'DEPARTMENT', 'DEPARTMENT_TREE', 'SUBSIDIARY', 'COMPANY', 'ALL') ),
    CONSTRAINT fk_rp_grant FOREIGN KEY (granted_by) REFERENCES iam_user (id)
);
CREATE UNIQUE INDEX uk_rp_role_perm ON iam_role_permission (role_id, permission_id);
CREATE INDEX idx_rp_perm_id ON iam_role_permission (permission_id);
CREATE INDEX idx_rp_data_scope ON iam_role_permission (data_scope);
CREATE INDEX idx_rp_grant_id ON iam_role_permission (granted_by);
CREATE INDEX idx_rp_exp_at ON iam_role_permission (expired_at);
CREATE INDEX idx_rp_created_by ON iam_role_permission (created_by);
CREATE INDEX idx_rp_updated_by ON iam_role_permission (updated_by);

CREATE TABLE iam_user_role
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    created_by INTEGER NULL,
    updated_by INTEGER NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ur_user FOREIGN KEY (user_id) REFERENCES iam_user (id),
    CONSTRAINT fk_ur_role FOREIGN KEY (role_id) REFERENCES iam_role (id)
);
CREATE UNIQUE INDEX uk_user_role ON iam_user_role (user_id, role_id);
CREATE INDEX idx_ur_role_id ON iam_user_role (role_id);
CREATE INDEX idx_ur_created_by ON iam_user_role (created_by);
CREATE INDEX idx_ur_updated_by ON iam_user_role (updated_by);

CREATE TABLE iam_user_permission
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    effect VARCHAR(16) NOT NULL DEFAULT 'ALLOW',
    data_scope VARCHAR(32) NULL,
    granted_by INTEGER NULL,
    expired_at TEXT NULL,
    created_by INTEGER NULL,
    updated_by INTEGER NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_up_user FOREIGN KEY (user_id) REFERENCES iam_user (id),
    CONSTRAINT fk_up_perm FOREIGN KEY (permission_id) REFERENCES iam_permission (id),
    CONSTRAINT fk_up_grant FOREIGN KEY (granted_by) REFERENCES iam_user (id),
    CONSTRAINT chk_up_data_scope CHECK ( data_scope IS NULL OR data_scope IN ('SELF', 'DEPARTMENT', 'DEPARTMENT_TREE', 'SUBSIDIARY', 'COMPANY', 'ALL') ),
    CONSTRAINT chk_up_effect CHECK (effect IN ('ALLOW', 'DENY'))
);
CREATE UNIQUE INDEX uk_up_user_perm ON iam_user_permission (user_id, permission_id);
CREATE INDEX idx_up_perm_id ON iam_user_permission (permission_id);
CREATE INDEX idx_up_data_scope ON iam_user_permission (data_scope);
CREATE INDEX idx_up_grant_id ON iam_user_permission (granted_by);
CREATE INDEX idx_up_exp_at ON iam_user_permission (expired_at);
CREATE INDEX idx_up_created_by ON iam_user_permission (created_by);
CREATE INDEX idx_up_updated_by ON iam_user_permission (updated_by);

CREATE TABLE iam_department_permission
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    effect VARCHAR(16) NOT NULL DEFAULT 'ALLOW',
    data_scope VARCHAR(32) NULL,
    granted_by INTEGER NULL,
    expired_at TEXT NULL,
    created_by INTEGER NULL,
    updated_by INTEGER NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_dp_dept FOREIGN KEY (department_id) REFERENCES iam_department (id),
    CONSTRAINT fk_dp_perm FOREIGN KEY (permission_id) REFERENCES iam_permission (id),
    CONSTRAINT fk_dp_grant FOREIGN KEY (granted_by) REFERENCES iam_user (id),
    CONSTRAINT chk_dp_data_scope CHECK ( data_scope IS NULL OR data_scope IN ('SELF', 'DEPARTMENT', 'DEPARTMENT_TREE', 'SUBSIDIARY', 'COMPANY', 'ALL') ),
    CONSTRAINT chk_dp_effect CHECK (effect IN ('ALLOW', 'DENY'))
);
CREATE UNIQUE INDEX uk_dp_dept_perm ON iam_department_permission (department_id, permission_id);
CREATE INDEX idx_dp_perm_id ON iam_department_permission (permission_id);
CREATE INDEX idx_dp_data_scope ON iam_department_permission (data_scope);
CREATE INDEX idx_dp_grant_id ON iam_department_permission (granted_by);
CREATE INDEX idx_dp_exp_at ON iam_department_permission (expired_at);
CREATE INDEX idx_dp_created_by ON iam_department_permission (created_by);
CREATE INDEX idx_dp_updated_by ON iam_department_permission (updated_by);

CREATE TABLE iam_subsidiary_permission
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subsidiary_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    effect VARCHAR(16) NOT NULL DEFAULT 'ALLOW',
    data_scope VARCHAR(32) NULL,
    granted_by INTEGER NULL,
    expired_at TEXT NULL,
    created_by INTEGER NULL,
    updated_by INTEGER NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sp_sub FOREIGN KEY (subsidiary_id) REFERENCES iam_subsidiary (id),
    CONSTRAINT fk_sp_perm FOREIGN KEY (permission_id) REFERENCES iam_permission (id),
    CONSTRAINT fk_sp_grant FOREIGN KEY (granted_by) REFERENCES iam_user (id),
    CONSTRAINT chk_sp_data_scope CHECK ( data_scope IS NULL OR data_scope IN ('SELF', 'DEPARTMENT', 'DEPARTMENT_TREE', 'SUBSIDIARY', 'COMPANY', 'ALL') ),
    CONSTRAINT chk_sp_effect CHECK (effect IN ('ALLOW', 'DENY'))
);
CREATE UNIQUE INDEX uk_sp_sub_perm ON iam_subsidiary_permission (subsidiary_id, permission_id);
CREATE INDEX idx_sp_perm_id ON iam_subsidiary_permission (permission_id);
CREATE INDEX idx_sp_data_scope ON iam_subsidiary_permission (data_scope);
CREATE INDEX idx_sp_grant_id ON iam_subsidiary_permission (granted_by);
CREATE INDEX idx_sp_exp_at ON iam_subsidiary_permission (expired_at);
CREATE INDEX idx_sp_created_by ON iam_subsidiary_permission (created_by);
CREATE INDEX idx_sp_updated_by ON iam_subsidiary_permission (updated_by);

CREATE TABLE iam_resource
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_type VARCHAR(128) NOT NULL,
    resource_name VARCHAR(128) NOT NULL,
    module_code VARCHAR(64) NOT NULL,
    status INTEGER NOT NULL DEFAULT 1,
    created_by INTEGER NULL,
    updated_by INTEGER NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_resource_status CHECK (status IN (0, 1))
);
CREATE UNIQUE INDEX uk_resource_type ON iam_resource (resource_type);
CREATE INDEX idx_resource_module_code ON iam_resource (module_code);
CREATE INDEX idx_resource_status ON iam_resource (status);
CREATE INDEX idx_resource_created_by ON iam_resource (created_by);
CREATE INDEX idx_resource_updated_by ON iam_resource (updated_by);

CREATE TABLE iam_resource_action
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_id INTEGER NOT NULL,
    action_code VARCHAR(64) NOT NULL,
    action_name VARCHAR(128) NOT NULL,
    status INTEGER NOT NULL DEFAULT 1,
    created_by INTEGER NULL,
    updated_by INTEGER NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_resource_action_resource FOREIGN KEY (resource_id) REFERENCES iam_resource (id),
    CONSTRAINT chk_resource_action_status CHECK (status IN (0, 1))
);
CREATE UNIQUE INDEX uk_resource_action_unique ON iam_resource_action (resource_id, action_code);
CREATE INDEX idx_resource_action_code ON iam_resource_action (action_code);
CREATE INDEX idx_resource_action_status ON iam_resource_action (status);
CREATE INDEX idx_resource_action_created_by ON iam_resource_action (created_by);
CREATE INDEX idx_resource_action_updated_by ON iam_resource_action (updated_by);

CREATE TABLE iam_resource_acl
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_type VARCHAR(32) NOT NULL,
    subject_id INTEGER NOT NULL,
    resource_type VARCHAR(128) NOT NULL,
    resource_id VARCHAR(128) NOT NULL,
    action_code VARCHAR(64) NOT NULL,
    effect VARCHAR(16) NOT NULL DEFAULT 'ALLOW',
    data_scope VARCHAR(32) NULL,
    expired_at TEXT NULL,
    created_by INTEGER NULL,
    updated_by INTEGER NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_resource_acl_subject_type CHECK (subject_type IN ('USER', 'ROLE', 'DEPARTMENT', 'ORGANIZATION', 'SUBSIDIARY')),
    CONSTRAINT chk_resource_acl_effect CHECK (effect IN ('ALLOW', 'DENY')),
    CONSTRAINT chk_resource_acl_data_scope CHECK (
        data_scope IS NULL
            OR data_scope IN (
                'SELF',
                'DEPARTMENT',
                'DEPARTMENT_TREE',
                'DEPARTMENT_AND_CHILDREN',
                'SUBSIDIARY',
                'COMPANY',
                'ORGANIZATION',
                'ALL'
            )
        )
);
CREATE UNIQUE INDEX uk_resource_acl_unique ON iam_resource_acl (subject_type, subject_id, resource_type, resource_id, action_code);
CREATE INDEX idx_resource_acl_resource_action ON iam_resource_acl (resource_type, resource_id, action_code);
CREATE INDEX idx_resource_acl_subject ON iam_resource_acl (subject_type, subject_id);
CREATE INDEX idx_resource_acl_effect ON iam_resource_acl (effect);
CREATE INDEX idx_resource_acl_expired_at ON iam_resource_acl (expired_at);

CREATE TABLE iam_resource_relation
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_type VARCHAR(128) NOT NULL,
    resource_id VARCHAR(128) NOT NULL,
    parent_resource_type VARCHAR(128) NOT NULL,
    parent_resource_id VARCHAR(128) NOT NULL,
    relation_type VARCHAR(32) NOT NULL DEFAULT 'PARENT',
    created_by INTEGER NULL,
    updated_by INTEGER NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_resource_relation_type CHECK (relation_type IN ('PARENT'))
);
CREATE UNIQUE INDEX uk_resource_relation_unique ON iam_resource_relation (resource_type, resource_id, parent_resource_type, parent_resource_id);
CREATE INDEX idx_resource_relation_resource ON iam_resource_relation (resource_type, resource_id);
CREATE INDEX idx_resource_relation_parent ON iam_resource_relation (parent_resource_type, parent_resource_id);

CREATE TABLE iam_policy
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_code VARCHAR(128) NOT NULL,
    policy_name VARCHAR(128) NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0,
    status INTEGER NOT NULL DEFAULT 1,
    version INTEGER NOT NULL DEFAULT 1,
    created_by INTEGER NULL,
    updated_by INTEGER NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_policy_status CHECK (status IN (0, 1))
);
CREATE UNIQUE INDEX uk_policy_code ON iam_policy (policy_code);
CREATE INDEX idx_policy_status_priority ON iam_policy (status, priority);

CREATE TABLE iam_policy_rule
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_id INTEGER NOT NULL,
    subject_type VARCHAR(32) NULL,
    subject_id INTEGER NULL,
    resource_type VARCHAR(128) NULL,
    resource_id VARCHAR(128) NULL,
    action_code VARCHAR(64) NOT NULL,
    effect VARCHAR(16) NOT NULL,
    data_scope VARCHAR(32) NULL,
    condition_json TEXT NULL,
    priority INTEGER NOT NULL DEFAULT 0,
    status INTEGER NOT NULL DEFAULT 1,
    created_by INTEGER NULL,
    updated_by INTEGER NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_policy_rule_policy FOREIGN KEY (policy_id) REFERENCES iam_policy (id),
    CONSTRAINT chk_policy_rule_subject_type CHECK (
        subject_type IS NULL OR subject_type IN ('USER', 'ROLE', 'DEPARTMENT', 'ORGANIZATION', 'SUBSIDIARY')
    ),
    CONSTRAINT chk_policy_rule_effect CHECK (effect IN ('ALLOW', 'DENY')),
    CONSTRAINT chk_policy_rule_data_scope CHECK (
        data_scope IS NULL
            OR data_scope IN (
                'SELF',
                'DEPARTMENT',
                'DEPARTMENT_TREE',
                'DEPARTMENT_AND_CHILDREN',
                'SUBSIDIARY',
                'COMPANY',
                'ORGANIZATION',
                'ALL'
            )
    ),
    CONSTRAINT chk_policy_rule_status CHECK (status IN (0, 1))
);
CREATE INDEX idx_policy_rule_policy ON iam_policy_rule (policy_id);
CREATE INDEX idx_policy_rule_status_priority ON iam_policy_rule (status, priority);
CREATE INDEX idx_policy_rule_subject_resource_action ON iam_policy_rule (subject_type, subject_id, resource_type, resource_id, action_code);

CREATE TABLE iam_login_failure_lock
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(64) NOT NULL,
    user_id INTEGER NULL,
    failed_count INTEGER NOT NULL DEFAULT 0,
    locked_until TEXT NULL,
    last_failed_at TEXT NULL,
    last_client_ip VARCHAR(64) NULL,
    last_user_agent VARCHAR(512) NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_lfl_user FOREIGN KEY (user_id) REFERENCES iam_user (id)
);
CREATE UNIQUE INDEX uk_lfl_username ON iam_login_failure_lock (username);
CREATE INDEX idx_lfl_user_id ON iam_login_failure_lock (user_id);
CREATE INDEX idx_lfl_locked_until ON iam_login_failure_lock (locked_until);

CREATE TABLE iam_operation_audit
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operator_id INTEGER NULL,
    company_id INTEGER NULL,
    operation_type VARCHAR(64) NOT NULL,
    resource_type VARCHAR(64) NOT NULL,
    resource_id INTEGER NULL,
    request_method VARCHAR(16) NULL,
    request_path VARCHAR(255) NULL,
    client_ip VARCHAR(64) NULL,
    user_agent VARCHAR(512) NULL,
    request_data TEXT NULL,
    before_data TEXT NULL,
    after_data TEXT NULL,
    extra_data TEXT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'SUCCESS',
    error_code INTEGER NULL,
    error_message VARCHAR(512) NULL,
    trace_id VARCHAR(64) NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audit_operator FOREIGN KEY (operator_id) REFERENCES iam_user (id),
    CONSTRAINT fk_audit_company FOREIGN KEY (company_id) REFERENCES iam_company (id),
    CONSTRAINT chk_audit_status CHECK (status IN ('SUCCESS', 'FAILED'))
);
CREATE INDEX idx_audit_operator_id ON iam_operation_audit (operator_id);
CREATE INDEX idx_audit_company_id ON iam_operation_audit (company_id);
CREATE INDEX idx_audit_resource ON iam_operation_audit (resource_type, resource_id);
CREATE INDEX idx_audit_operation_type ON iam_operation_audit (operation_type);
CREATE INDEX idx_audit_status ON iam_operation_audit (status);
CREATE INDEX idx_audit_trace_id ON iam_operation_audit (trace_id);
CREATE INDEX idx_audit_created_at ON iam_operation_audit (created_at);

CREATE TABLE iam_audit_log
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operator_id INTEGER NULL,
    subject_type VARCHAR(32) NOT NULL,
    subject_id INTEGER NOT NULL,
    resource_type VARCHAR(128) NOT NULL,
    resource_id VARCHAR(128) NOT NULL,
    action_code VARCHAR(64) NOT NULL,
    result VARCHAR(16) NOT NULL,
    reason VARCHAR(512) NOT NULL,
    matched_acl_id INTEGER NULL,
    matched_policy_id INTEGER NULL,
    matched_rule_id INTEGER NULL,
    matched_source VARCHAR(32) NULL,
    trace_id VARCHAR(64) NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_decision_audit_operator FOREIGN KEY (operator_id) REFERENCES iam_user (id),
    CONSTRAINT chk_decision_audit_subject_type CHECK (subject_type IN ('USER', 'ROLE', 'DEPARTMENT', 'ORGANIZATION', 'SUBSIDIARY')),
    CONSTRAINT chk_decision_audit_result CHECK (result IN ('ALLOW', 'DENY'))
);
CREATE INDEX idx_decision_audit_subject ON iam_audit_log (subject_type, subject_id);
CREATE INDEX idx_decision_audit_resource_action ON iam_audit_log (resource_type, resource_id, action_code);
CREATE INDEX idx_decision_audit_result ON iam_audit_log (result);
CREATE INDEX idx_decision_audit_matched_acl ON iam_audit_log (matched_acl_id);
CREATE INDEX idx_decision_audit_matched_source ON iam_audit_log (matched_source);
CREATE INDEX idx_decision_audit_trace_id ON iam_audit_log (trace_id);
CREATE INDEX idx_decision_audit_created_at ON iam_audit_log (created_at);

CREATE TABLE iam_user_device
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    device_id VARCHAR(128) NOT NULL,
    device_name VARCHAR(128) NOT NULL,
    device_type VARCHAR(32) NOT NULL,
    os_name VARCHAR(64) DEFAULT NULL,
    browser_name VARCHAR(64) DEFAULT NULL,
    fingerprint_hash VARCHAR(128) NOT NULL,
    trusted INTEGER NOT NULL DEFAULT 0,
    status INTEGER NOT NULL DEFAULT 1,
    first_login_at TEXT NOT NULL,
    last_active_at TEXT NOT NULL,
    last_client_ip VARCHAR(64) DEFAULT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT fk_ud_user FOREIGN KEY (user_id) REFERENCES iam_user (id)
);
CREATE UNIQUE INDEX uk_device_id ON iam_user_device (device_id);
CREATE UNIQUE INDEX uk_user_fingerprint ON iam_user_device (user_id, fingerprint_hash);
CREATE INDEX idx_ud_user_id ON iam_user_device (user_id);
CREATE INDEX idx_ud_user_fingerprint ON iam_user_device (user_id, fingerprint_hash);
CREATE INDEX idx_ud_last_active_at ON iam_user_device (last_active_at);
CREATE INDEX idx_ud_status ON iam_user_device (status);

CREATE TABLE iam_user_session
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    device_id INTEGER NOT NULL,
    session_id VARCHAR(64) NOT NULL,
    login_ip VARCHAR(64) DEFAULT NULL,
    user_agent TEXT DEFAULT NULL,
    risk_level INTEGER NOT NULL DEFAULT 0,
    last_active_at TEXT NOT NULL,
    expired_at TEXT NOT NULL,
    revoked_at TEXT DEFAULT NULL,
    created_at TEXT NOT NULL,
    CONSTRAINT fk_us_user FOREIGN KEY (user_id) REFERENCES iam_user (id),
    CONSTRAINT fk_us_device FOREIGN KEY (device_id) REFERENCES iam_user_device (id)
);
CREATE UNIQUE INDEX uk_session_id ON iam_user_session (session_id);
CREATE INDEX idx_us_user_id ON iam_user_session (user_id);
CREATE INDEX idx_us_device_id ON iam_user_session (device_id);
CREATE INDEX idx_us_expired_at ON iam_user_session (expired_at);
CREATE INDEX idx_us_revoked_at ON iam_user_session (revoked_at);
CREATE INDEX idx_us_user_active ON iam_user_session (user_id, revoked_at, expired_at);

CREATE TABLE iam_user_token
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id INTEGER NULL,
    refresh_token_hash CHAR(64) NOT NULL,
    access_jti VARCHAR(64) NULL,
    refresh_jti VARCHAR(64) NOT NULL,
    client_ip VARCHAR(64) NULL,
    user_agent VARCHAR(512) NULL,
    expired_at TEXT NOT NULL,
    revoked_at TEXT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ut_user FOREIGN KEY (user_id) REFERENCES iam_user (id),
    CONSTRAINT fk_ut_session FOREIGN KEY (session_id) REFERENCES iam_user_session (id)
);
CREATE UNIQUE INDEX uk_ut_refresh_jti ON iam_user_token (refresh_jti);
CREATE UNIQUE INDEX uk_ut_refresh_token_hash ON iam_user_token (refresh_token_hash);
CREATE UNIQUE INDEX uk_ut_user_access_jti ON iam_user_token (user_id, access_jti);
CREATE INDEX idx_ut_user_id ON iam_user_token (user_id);
CREATE INDEX idx_ut_session_id ON iam_user_token (session_id);
CREATE INDEX idx_ut_access_jti ON iam_user_token (access_jti);
CREATE INDEX idx_ut_exp_at ON iam_user_token (expired_at);

INSERT INTO iam_permission
(permission_code, permission_name, permission_type, parent_id, status, created_at, updated_at)
VALUES ('iam:user:update_staff', '修改后台用户标识', 'ACTION', NULL, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
       ('iam:user:update_superuser', '修改超级管理员标识', 'ACTION', NULL, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
