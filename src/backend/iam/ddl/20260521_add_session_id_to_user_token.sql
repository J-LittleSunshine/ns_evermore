ALTER TABLE iam_user_token
    ADD COLUMN session_id BIGINT UNSIGNED NULL COMMENT '会话ID' AFTER user_id,
    ADD KEY idx_ut_session_id (session_id),
    ADD CONSTRAINT fk_ut_session
        FOREIGN KEY (session_id) REFERENCES iam_user_session (id);
