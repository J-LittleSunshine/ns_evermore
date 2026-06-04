# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ns_common.storage import NsObjectStorageClient

if TYPE_CHECKING:
    pass

def main() -> None:
    """Smoke test local filesystem object storage backend."""
    client = NsObjectStorageClient.get_default()

    client.ensure_bucket()

    object_info = client.put_bytes(
        object_name="smoke/hello.txt",
        data=b"hello local object storage",
        content_type="text/plain",
        metadata={
            "ns-module": "smoke",
            "ns-resource-type": "object-storage",
        },
    )
    print("uploaded:", object_info)

    data = client.get_bytes(object_name="smoke/hello.txt")
    print("downloaded:", data.decode("utf-8"))

    stat = client.stat_object(object_name="smoke/hello.txt")
    print("stat:", stat)

    objects = client.list_objects(prefix="smoke")
    print("listed:", objects)

    download_path = Path("tmp/object_storage_local_smoke/hello.txt")
    client.get_file(object_name="smoke/hello.txt", file_path=download_path)
    print("download_file:", download_path)

    removed = client.remove_object(object_name="smoke/hello.txt")
    print("removed:", removed)

    client.close()


if __name__ == "__main__":
    main()
