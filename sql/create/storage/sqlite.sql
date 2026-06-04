CREATE TABLE storage_object_ref
(
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    bucket            VARCHAR(63)   NOT NULL,
    object_name       VARCHAR(1024) NOT NULL,
    backend           VARCHAR(32)   NOT NULL,
    module_code       VARCHAR(64)   NOT NULL,
    resource_type     VARCHAR(128)  NOT NULL,
    resource_id       VARCHAR(128)  NULL,
    original_filename VARCHAR(255)  NULL,
    content_type      VARCHAR(128)  NULL,
    object_size       INTEGER       NULL,
    etag              VARCHAR(128)  NULL,
    sha256            VARCHAR(64)   NULL,
    version_id        VARCHAR(128)  NULL,
    metadata_json     TEXT          NOT NULL DEFAULT '{}',
    created_by        INTEGER       NULL,
    updated_by        INTEGER       NULL,
    created_at        TEXT          NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TEXT          NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at        TEXT          NULL
);
CREATE UNIQUE INDEX uk_storage_obj_ref_bucket_name ON storage_object_ref (bucket, object_name);
CREATE INDEX idx_storage_obj_ref_res ON storage_object_ref (module_code, resource_type, resource_id);
CREATE INDEX idx_storage_obj_ref_sha256 ON storage_object_ref (sha256);
CREATE INDEX idx_storage_obj_ref_created ON storage_object_ref (created_at);
CREATE INDEX idx_storage_obj_ref_deleted ON storage_object_ref (deleted_at);
