CREATE TABLE storage_object_ref
(
    id                BIGINT IDENTITY(1, 1) PRIMARY KEY,
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
    metadata_json     CLOB          NOT NULL,
    created_by        BIGINT        NULL,
    updated_by        BIGINT        NULL,
    created_at        TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at        TIMESTAMP     NULL
);

CREATE UNIQUE INDEX uk_storage_obj_ref_bucket_name ON storage_object_ref (bucket, object_name);
CREATE INDEX idx_storage_obj_ref_res ON storage_object_ref (module_code, resource_type, resource_id);
CREATE INDEX idx_storage_obj_ref_sha256 ON storage_object_ref (sha256);
CREATE INDEX idx_storage_obj_ref_created ON storage_object_ref (created_at);
CREATE INDEX idx_storage_obj_ref_deleted ON storage_object_ref (deleted_at);
