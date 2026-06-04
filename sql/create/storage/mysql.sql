CREATE TABLE storage_object_ref
(
    id                BIGINT        NOT NULL AUTO_INCREMENT,
    bucket            VARCHAR(63)   NOT NULL,
    object_name       VARCHAR(1024) NOT NULL,
    backend           VARCHAR(32)   NOT NULL,
    module_code       VARCHAR(64)   NOT NULL,
    resource_type     VARCHAR(128)  NOT NULL,
    resource_id       VARCHAR(128)  NULL,
    original_filename VARCHAR(255)  NULL,
    content_type      VARCHAR(128)  NULL,
    object_size       BIGINT        NULL,
    etag              VARCHAR(128)  NULL,
    sha256            VARCHAR(64)   NULL,
    version_id        VARCHAR(128)  NULL,
    metadata_json     JSON          NOT NULL,
    created_by        BIGINT        NULL,
    updated_by        BIGINT        NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    deleted_at DATETIME(6) NULL,
    PRIMARY KEY (id)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci;

CREATE UNIQUE INDEX uk_storage_obj_ref_bucket_name ON storage_object_ref (bucket, object_name(512));
CREATE INDEX idx_storage_obj_ref_res ON storage_object_ref (module_code, resource_type, resource_id);
CREATE INDEX idx_storage_obj_ref_sha256 ON storage_object_ref (sha256);
CREATE INDEX idx_storage_obj_ref_created ON storage_object_ref (created_at);
CREATE INDEX idx_storage_obj_ref_deleted ON storage_object_ref (deleted_at);
