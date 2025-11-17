import logging
import os
from io import BytesIO
from typing import BinaryIO
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)

S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")

_session = boto3.Session()

# local minio overrides the S3_ENDPOINT_URL to localhost:9001
if S3_ENDPOINT_URL:
  _s3 = _session.client(
      "s3",
      endpoint_url=settings.S3_ENDPOINT_URL,
      aws_access_key_id=settings.S3_ACCESS_KEY,
      aws_secret_access_key=settings.S3_SECRET_KEY,
      region_name=settings.S3_REGION_NAME,
  )
else:
    _s3 = _session.client(
      "s3",
      aws_access_key_id=settings.S3_ACCESS_KEY,
      aws_secret_access_key=settings.S3_SECRET_KEY,
      region_name=settings.S3_REGION_NAME,
  )


def upload_fileobj(
    file_obj: BinaryIO,
    key: str,
    content_type: str = "application/octet-stream",
) -> str:
  # print(f"{settings.S3_ENDPOINT_URL} {settings.S3_ACCESS_KEY} {settings.S3_SECRET_KEY}")
  _s3.upload_fileobj(
      Fileobj=file_obj,
      Bucket=settings.S3_BUCKET,
      Key=key,
      ExtraArgs={"ContentType": content_type},
  )
  logger.info("Uploaded object to S3: bucket=%s key=%s",
              settings.S3_BUCKET, key)
  return key


def upload_bytes(
    data: bytes,
    key: str,
    content_type: str = "application/octet-stream",
) -> str:
  file_obj = BytesIO(data)
  return upload_fileobj(file_obj=file_obj, key=key, content_type=content_type)


def generate_presigned_url(key: str, expires_in: int = 3600) -> str:
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
    return key


def download_fileobj(key: str) -> BytesIO | None:
  buffer = BytesIO()

  try:
    _s3.download_fileobj(
        Bucket=settings.S3_BUCKET,
        Key=key,
        Fileobj=buffer
    )
    buffer.seek(0)
    logger.info("Downloaded object from S3: bucket=%s key=%s",
                settings.S3_BUCKET, key)
    return buffer

  except ClientError as exc:
    error_code = exc.response.get("Error", {}).get("Code")
    if error_code == "NoSuchKey":
      logger.warning("S3 object not found: %s", key)
      return None

    logger.error("Failed to download S3 object key=%s: %s", key, exc)
    raise


def get_object_key(campaign_id: int, product_id: int, ratio: str) -> str:
  # helper method to keep object keys consistent
  # save objects in similar structure:
  # /campaign_id/product_id/aspect_ratio/asset.png
  safe_ratio = ratio.replace(":", "x")
  timestamp = int(datetime.utcnow().timestamp())
  key = (
      f"campaign_{campaign_id}/product_{product_id}/"
      f"{safe_ratio}/creative_{timestamp}.png"
  )
  return key