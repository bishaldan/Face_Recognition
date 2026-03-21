import boto3
from botocore.client import BaseClient
from botocore.exceptions import ClientError

from app.core.config import Settings
from app.services.storage.base import StoredObject


class S3StorageService:
    backend_name = "s3"

    def __init__(self, settings: Settings):
        self.bucket = settings.storage_bucket
        self.client: BaseClient = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.storage_region,
            use_ssl=settings.s3_secure,
        )

    def initialize(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError:
            self.client.create_bucket(Bucket=self.bucket)

    def store_image(self, *, object_key: str, content: bytes, content_type: str) -> StoredObject:
        self.client.put_object(
            Bucket=self.bucket,
            Key=object_key,
            Body=content,
            ContentType=content_type,
        )
        return StoredObject(
            object_key=object_key,
            content_type=content_type,
            size_bytes=len(content),
        )

    def fetch_bytes(self, object_key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=object_key)
        return response["Body"].read()
