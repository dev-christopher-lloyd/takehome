import logging
from io import BytesIO
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)

_session = boto3.Session()

_s3 = _session.client(
    "s3",
    endpoint_url=settings.S3_ENDPOINT_URL,
    aws_access_key_id=settings.S3_ACCESS_KEY,
    aws_secret_access_key=settings.S3_SECRET_KEY,
    region_name=settings.S3_REGION_NAME,
)

def upload_fileobj(
    file_obj: BinaryIO,
    key: str,
    content_type: str = "application/octet-stream",
) -> str:
    """
    Upload a file-like object to S3-compatible storage.

    Returns the S3 key (path) for later retrieval.
    """
    # print(f"{settings.S3_ENDPOINT_URL} {settings.S3_ACCESS_KEY} {settings.S3_SECRET_KEY}")
    _s3.upload_fileobj(
        Fileobj=file_obj,
        Bucket=settings.S3_BUCKET,
        Key=key,
        ExtraArgs={"ContentType": content_type},
    )
    logger.info("Uploaded object to S3: bucket=%s key=%s", settings.S3_BUCKET, key)
    return key


def upload_bytes(
    data: bytes,
    key: str,
    content_type: str = "application/octet-stream",
) -> str:
    """
    Convenience wrapper to upload raw bytes.
    """
    file_obj = BytesIO(data)
    return upload_fileobj(file_obj=file_obj, key=key, content_type=content_type)


def generate_presigned_url(key: str, expires_in: int = 3600) -> str:
    """
    Generate a time-limited URL for accessing an object.

    For browser-based previews of generated creatives.
    """
    try:
        url = _s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": settings.S3_BUCKET, "Key": key},
            ExpiresIn=expires_in,
        )
        return url
    except ClientError as exc:
        logger.error(
            "Failed to generate presigned URL for key=%s: %s",
            key,
            exc,
        )
        # In a real app you might raise a custom error; for the POC, fall back
        # to returning the key, which is at least useful for debugging.
        return key
