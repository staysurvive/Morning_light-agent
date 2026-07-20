from types import SimpleNamespace

from src.infra import minio_client


class FakeResponse:
    def __init__(self, payload: bytes):
        self.payload = payload
        self.closed = False
        self.released = False

    def read(self) -> bytes:
        return self.payload

    def close(self) -> None:
        self.closed = True

    def release_conn(self) -> None:
        self.released = True


class FakeMinio:
    def __init__(self):
        self.bucket_created = False
        self.upload = None
        self.deleted = None
        self.response = FakeResponse(b"stored")

    def bucket_exists(self, bucket_name):
        return False

    def make_bucket(self, bucket_name):
        self.bucket_created = bucket_name

    def put_object(self, **kwargs):
        self.upload = kwargs

    def get_object(self, bucket_name, object_name):
        return self.response

    def remove_object(self, bucket_name, object_name):
        self.deleted = (bucket_name, object_name)

    def list_objects(self, bucket_name, recursive):
        return [SimpleNamespace(size=3), SimpleNamespace(size=5)]


def test_minio_adapter_uses_valid_sdk_arguments(monkeypatch):
    fake = FakeMinio()
    monkeypatch.setattr(minio_client, "_minio_client", fake)

    assert minio_client.ensure_bucket_exists() is True
    assert fake.bucket_created == minio_client.settings.MINIO_BUCKET

    object_name = minio_client.upload_file("kb/test.txt", b"hello", "text/plain")
    assert object_name == "kb/test.txt"
    assert fake.upload["length"] == 5
    assert fake.upload["data"].read() == b"hello"

    assert minio_client.download_file(object_name) == b"stored"
    assert fake.response.closed and fake.response.released

    minio_client.delete_object(object_name)
    assert fake.deleted == (minio_client.settings.MINIO_BUCKET, object_name)

    usage = minio_client.get_bucket_usage()
    assert usage.object_count == 2
    assert usage.size_bytes == 8
