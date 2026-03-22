import uuid
import boto3
from botocore.exceptions import ClientError
from typing import Optional, BinaryIO
from fastapi import UploadFile

from app.config import settings


class FileService:
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
            endpoint_url=settings.s3_endpoint_url,
        )
        self.bucket_name = settings.s3_bucket_name

    async def ensure_bucket_exists(self):
        """Create bucket if it doesn't exist (for local MinIO)."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            self.s3_client.create_bucket(Bucket=self.bucket_name)

    def _generate_key(self, folder: str, filename: str) -> str:
        """Generate a unique S3 key for the file."""
        ext = filename.split(".")[-1] if "." in filename else ""
        unique_name = f"{uuid.uuid4()}.{ext}" if ext else str(uuid.uuid4())
        return f"{folder}/{unique_name}"

    async def upload_file(
        self,
        file: UploadFile,
        folder: str = "uploads",
    ) -> str:
        """Upload a file to S3 and return the URL."""
        await self.ensure_bucket_exists()

        key = self._generate_key(folder, file.filename or "file")
        content = await file.read()

        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=content,
            ContentType=file.content_type or "application/octet-stream",
        )

        if settings.s3_endpoint_url:
            url = f"{settings.s3_endpoint_url}/{self.bucket_name}/{key}"
        else:
            url = f"https://{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com/{key}"

        return url

    async def upload_bytes(
        self,
        content: bytes,
        filename: str,
        folder: str = "uploads",
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload raw bytes to S3 and return the URL."""
        await self.ensure_bucket_exists()

        key = self._generate_key(folder, filename)

        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=content,
            ContentType=content_type,
        )

        if settings.s3_endpoint_url:
            url = f"{settings.s3_endpoint_url}/{self.bucket_name}/{key}"
        else:
            url = f"https://{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com/{key}"

        return url

    async def delete_file(self, url: str) -> bool:
        """Delete a file from S3 by its URL."""
        try:
            if settings.s3_endpoint_url:
                key = url.replace(f"{settings.s3_endpoint_url}/{self.bucket_name}/", "")
            else:
                key = url.split(f"{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com/")[-1]

            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False

    async def get_presigned_url(
        self,
        key: str,
        expiration: int = 3600,
    ) -> str:
        """Generate a presigned URL for downloading a file."""
        return self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": key},
            ExpiresIn=expiration,
        )


file_service = FileService()
