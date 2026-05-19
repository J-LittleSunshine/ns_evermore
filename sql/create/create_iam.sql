CREATE TABLE iam_company
(
    id           BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '公司ID',
    company_code VARCHAR(64)  NOT NULL COMMENT '公司编码',
    company_name VARCHAR(128) NOT NULL COMMENT '公司名称',
    legal_name   VARCHAR(128) NULL COMMENT '公司法定名称',
    status       TINYINT      NOT NULL DEFAULT 1 COMMENT '状态：1启用，0禁用',
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    UNIQUE KEY uk_comp_code (company_code),

    CONSTRAINT chk_comp_stat CHECK (status IN (0, 1))
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='公司信息表';


CREATE TABLE iam_subsidiary
(
    id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '子公司ID',
    company_id      BIGINT UNSIGNED NOT NULL COMMENT '所属公司ID',
    subsidiary_code VARCHAR(64)     NOT NULL COMMENT '子公司编码',
    subsidiary_name VARCHAR(128)    NOT NULL COMMENT '子公司名称',
    status          TINYINT         NOT NULL DEFAULT 1 COMMENT '状态：1启用，0禁用',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    UNIQUE KEY uk_sub_code (subsidiary_code),

    KEY idx_sub_comp_id (company_id),

    CONSTRAINT fk_sub_comp
        FOREIGN KEY (company_id) REFERENCES iam_company (id),

    CONSTRAINT chk_sub_stat
        CHECK (status IN (0, 1))
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='子公司信息表';


CREATE TABLE iam_department
(
    id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '部门ID',
    company_id      BIGINT UNSIGNED NOT NULL COMMENT '所属公司ID',
    subsidiary_id   BIGINT UNSIGNED NULL COMMENT '所属子公司ID',
    parent_id       BIGINT UNSIGNED NULL COMMENT '父部门ID',
    department_code VARCHAR(64)     NOT NULL COMMENT '部门编码',
    department_name VARCHAR(128)    NOT NULL COMMENT '部门名称',
    status          TINYINT         NOT NULL DEFAULT 1 COMMENT '状态：1启用，0禁用',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    UNIQUE KEY uk_dept_code (department_code),

    KEY idx_dept_comp_id (company_id),
    KEY idx_dept_sub_id (subsidiary_id),
    KEY idx_dept_par_id (parent_id),

    CONSTRAINT fk_dept_comp
        FOREIGN KEY (company_id) REFERENCES iam_company (id),

    CONSTRAINT fk_dept_sub
        FOREIGN KEY (subsidiary_id) REFERENCES iam_subsidiary (id),

    CONSTRAINT fk_dept_par
        FOREIGN KEY (parent_id) REFERENCES iam_department (id),

    CONSTRAINT chk_dept_stat
        CHECK (status IN (0, 1))
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='部门信息表';


CREATE TABLE iam_user
(
    id            BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    username      VARCHAR(64)     NOT NULL COMMENT '用户名',
    password      VARCHAR(128)    NOT NULL COMMENT '密码哈希',
    email         VARCHAR(128)    NULL COMMENT '邮箱',
    phone         VARCHAR(32)     NULL COMMENT '手机号',
    display_name  VARCHAR(64)     NULL COMMENT '显示名称',

    user_type     VARCHAR(32)     NOT NULL COMMENT '用户类型',
    company_id    BIGINT UNSIGNED NULL COMMENT '所属公司ID',
    subsidiary_id BIGINT UNSIGNED NULL COMMENT '所属子公司ID',
    department_id BIGINT UNSIGNED NULL COMMENT '所属部门ID',

    is_active     TINYINT         NOT NULL DEFAULT 1 COMMENT '是否启用',
    is_staff      TINYINT         NOT NULL DEFAULT 0 COMMENT '是否后台用户',
    is_superuser  TINYINT         NOT NULL DEFAULT 0 COMMENT '是否超级管理员',

    last_login    DATETIME        NULL COMMENT '最后登录时间',
    created_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    UNIQUE KEY uk_user_name (username),
    UNIQUE KEY uk_user_email (email),
    UNIQUE KEY uk_user_phone (phone),

    KEY idx_user_type (user_type),
    KEY idx_user_comp_id (company_id),
    KEY idx_user_sub_id (subsidiary_id),
    KEY idx_user_dept_id (department_id),

    CONSTRAINT fk_user_comp
        FOREIGN KEY (company_id) REFERENCES iam_company (id),

    CONSTRAINT fk_user_sub
        FOREIGN KEY (subsidiary_id) REFERENCES iam_subsidiary (id),

    CONSTRAINT fk_user_dept
        FOREIGN KEY (department_id) REFERENCES iam_department (id),

    CONSTRAINT chk_user_type
        CHECK (user_type IN ('PERSONAL', 'ENTERPRISE')),

    CONSTRAINT chk_user_act
        CHECK (is_active IN (0, 1)),

    CONSTRAINT chk_user_staff
        CHECK (is_staff IN (0, 1)),

    CONSTRAINT chk_user_super
        CHECK (is_superuser IN (0, 1))
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='用户信息表';


CREATE TABLE iam_permission
(
    id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '权限ID',
    permission_code VARCHAR(128)    NOT NULL COMMENT '权限编码',
    permission_name VARCHAR(128)    NOT NULL COMMENT '权限名称',
    permission_type VARCHAR(32)     NOT NULL COMMENT '权限类型',
    parent_id       BIGINT UNSIGNED NULL COMMENT '父权限ID',
    status          TINYINT         NOT NULL DEFAULT 1 COMMENT '状态',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    UNIQUE KEY uk_perm_code (permission_code),

    KEY idx_perm_par_id (parent_id),

    CONSTRAINT fk_perm_par
        FOREIGN KEY (parent_id) REFERENCES iam_permission (id),

    CONSTRAINT chk_perm_type
        CHECK (permission_type IN ('MENU', 'ACTION', 'DATA')),

    CONSTRAINT chk_perm_stat
        CHECK (status IN (0, 1))
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='权限信息表';


CREATE TABLE iam_role
(
    id         BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '角色ID',
    role_code  VARCHAR(64)  NOT NULL COMMENT '角色编码',
    role_name  VARCHAR(128) NOT NULL COMMENT '角色名称',
    role_scope VARCHAR(32)  NOT NULL COMMENT '角色范围',
    status     TINYINT      NOT NULL DEFAULT 1 COMMENT '状态',
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    UNIQUE KEY uk_role_code (role_code),

    KEY idx_role_scope (role_scope),

    CONSTRAINT chk_role_scope
        CHECK (role_scope IN ('PERSONAL', 'ENTERPRISE')),

    CONSTRAINT chk_role_stat
        CHECK (status IN (0, 1))
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='角色信息表';


CREATE TABLE iam_role_permission
(
    id            BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',
    role_id       BIGINT UNSIGNED NOT NULL COMMENT '角色ID',
    permission_id BIGINT UNSIGNED NOT NULL COMMENT '权限ID',
    granted_by    BIGINT UNSIGNED NULL COMMENT '授权人ID',
    expired_at    DATETIME        NULL COMMENT '过期时间',
    created_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    UNIQUE KEY uk_rp_role_perm (role_id, permission_id),

    KEY idx_rp_perm_id (permission_id),
    KEY idx_rp_grant_id (granted_by),
    KEY idx_rp_exp_at (expired_at),

    CONSTRAINT fk_rp_role
        FOREIGN KEY (role_id) REFERENCES iam_role (id),

    CONSTRAINT fk_rp_perm
        FOREIGN KEY (permission_id) REFERENCES iam_permission (id),

    CONSTRAINT fk_rp_grant
        FOREIGN KEY (granted_by) REFERENCES iam_user (id)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='角色权限关系表';


CREATE TABLE iam_user_role
(
    id         BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',
    user_id    BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
    role_id    BIGINT UNSIGNED NOT NULL COMMENT '角色ID',
    created_at DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    UNIQUE KEY uk_user_role (user_id, role_id),

    KEY idx_ur_role_id (role_id),

    CONSTRAINT fk_ur_user
        FOREIGN KEY (user_id) REFERENCES iam_user (id),

    CONSTRAINT fk_ur_role
        FOREIGN KEY (role_id) REFERENCES iam_role (id)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='用户角色关系表';


CREATE TABLE iam_user_permission
(
    id            BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',
    user_id       BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
    permission_id BIGINT UNSIGNED NOT NULL COMMENT '权限ID',
    effect        VARCHAR(16)     NOT NULL DEFAULT 'ALLOW' COMMENT '权限效果',
    granted_by    BIGINT UNSIGNED NULL COMMENT '授权人ID',
    expired_at    DATETIME        NULL COMMENT '过期时间',
    created_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    UNIQUE KEY uk_up_user_perm (user_id, permission_id),

    KEY idx_up_perm_id (permission_id),
    KEY idx_up_grant_id (granted_by),
    KEY idx_up_exp_at (expired_at),

    CONSTRAINT fk_up_user
        FOREIGN KEY (user_id) REFERENCES iam_user (id),

    CONSTRAINT fk_up_perm
        FOREIGN KEY (permission_id) REFERENCES iam_permission (id),

    CONSTRAINT fk_up_grant
        FOREIGN KEY (granted_by) REFERENCES iam_user (id),

    CONSTRAINT chk_up_effect
        CHECK (effect IN ('ALLOW', 'DENY'))
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='用户直接权限表';


CREATE TABLE iam_department_permission
(
    id            BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',
    department_id BIGINT UNSIGNED NOT NULL COMMENT '部门ID',
    permission_id BIGINT UNSIGNED NOT NULL COMMENT '权限ID',
    effect        VARCHAR(16)     NOT NULL DEFAULT 'ALLOW' COMMENT '权限效果',
    granted_by    BIGINT UNSIGNED NULL COMMENT '授权人ID',
    expired_at    DATETIME        NULL COMMENT '过期时间',
    created_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    UNIQUE KEY uk_dp_dept_perm (department_id, permission_id),

    KEY idx_dp_perm_id (permission_id),
    KEY idx_dp_grant_id (granted_by),
    KEY idx_dp_exp_at (expired_at),

    CONSTRAINT fk_dp_dept
        FOREIGN KEY (department_id) REFERENCES iam_department (id),

    CONSTRAINT fk_dp_perm
        FOREIGN KEY (permission_id) REFERENCES iam_permission (id),

    CONSTRAINT fk_dp_grant
        FOREIGN KEY (granted_by) REFERENCES iam_user (id),

    CONSTRAINT chk_dp_effect
        CHECK (effect IN ('ALLOW', 'DENY'))
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='部门权限表';


CREATE TABLE iam_subsidiary_permission
(
    id            BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',
    subsidiary_id BIGINT UNSIGNED NOT NULL COMMENT '子公司ID',
    permission_id BIGINT UNSIGNED NOT NULL COMMENT '权限ID',
    effect        VARCHAR(16)     NOT NULL DEFAULT 'ALLOW' COMMENT '权限效果',
    granted_by    BIGINT UNSIGNED NULL COMMENT '授权人ID',
    expired_at    DATETIME        NULL COMMENT '过期时间',
    created_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    UNIQUE KEY uk_sp_sub_perm (subsidiary_id, permission_id),

    KEY idx_sp_perm_id (permission_id),
    KEY idx_sp_grant_id (granted_by),
    KEY idx_sp_exp_at (expired_at),

    CONSTRAINT fk_sp_sub
        FOREIGN KEY (subsidiary_id) REFERENCES iam_subsidiary (id),

    CONSTRAINT fk_sp_perm
        FOREIGN KEY (permission_id) REFERENCES iam_permission (id),

    CONSTRAINT fk_sp_grant
        FOREIGN KEY (granted_by) REFERENCES iam_user (id),

    CONSTRAINT chk_sp_effect
        CHECK (effect IN ('ALLOW', 'DENY'))
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='子公司权限表';

CREATE TABLE iam_user_token
(
    id            BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT 'ID',
    user_id       BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
    refresh_token VARCHAR(512)    NOT NULL COMMENT '刷新Token',
    access_jti    VARCHAR(64)     NULL COMMENT 'Access Token唯一ID',
    refresh_jti   VARCHAR(64)     NOT NULL COMMENT 'Refresh Token唯一ID',
    client_ip     VARCHAR(64)     NULL COMMENT '客户端IP',
    user_agent    VARCHAR(512)    NULL COMMENT '用户代理',
    expired_at    DATETIME        NOT NULL COMMENT '过期时间',
    revoked_at    DATETIME        NULL COMMENT '吊销时间',
    created_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    UNIQUE KEY uk_ut_refresh_jti (refresh_jti),
    KEY idx_ut_user_id (user_id),
    KEY idx_ut_access_jti (access_jti),
    KEY idx_ut_exp_at (expired_at),

    CONSTRAINT fk_ut_user
        FOREIGN KEY (user_id) REFERENCES iam_user (id)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='用户Token表';
