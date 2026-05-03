"""S3 I/O adapter for the Excel pipeline cloud execution."""

from __future__ import annotations

import logging
from pathlib import Path

import boto3
import botocore.exceptions

logger = logging.getLogger(__name__)

_MODULE = "cloud.s3_io"


def download_s3_prefix(
    bucket: str,
    prefix: str,
    local_dir: Path,
) -> list[Path]:
    """Download all real files under an S3 prefix to local_dir; return local paths."""
    local_dir = Path(local_dir)
    local_dir.mkdir(parents=True, exist_ok=True)
    prefix = _normalise_prefix(prefix)

    client = boto3.client("s3")
    _check_bucket(client, bucket)

    keys = _list_keys(client, bucket, prefix)
    if not keys:
        raise FileNotFoundError(
            f"[{_MODULE}] No downloadable files found at s3://{bucket}/{prefix}"
        )

    downloaded: list[Path] = []
    for key in keys:
        relative = key[len(prefix):]
        local_path = local_dir / relative
        local_path.parent.mkdir(parents=True, exist_ok=True)
        client.download_file(bucket, key, str(local_path))
        logger.info("[%s] Downloaded s3://%s/%s -> %s", _MODULE, bucket, key, local_path)
        downloaded.append(local_path)

    return downloaded


def download_s3_file(
    bucket: str,
    key: str,
    local_path: Path,
) -> Path:
    """Download a single S3 object to local_path; return local_path."""
    local_path = Path(local_path)
    local_path.parent.mkdir(parents=True, exist_ok=True)

    client = boto3.client("s3")
    _check_bucket(client, bucket)
    _check_key(client, bucket, key)

    client.download_file(bucket, key, str(local_path))
    logger.info("[%s] Downloaded s3://%s/%s -> %s", _MODULE, bucket, key, local_path)
    return local_path


def upload_directory(
    bucket: str,
    prefix: str,
    local_dir: Path,
) -> list[str]:
    """Upload all files from local_dir to s3://bucket/prefix/; return uploaded S3 keys."""
    local_dir = Path(local_dir)
    if not local_dir.exists():
        raise FileNotFoundError(
            f"[{_MODULE}] Local directory does not exist: {local_dir}"
        )

    prefix = _normalise_prefix(prefix)
    client = boto3.client("s3")
    _check_bucket(client, bucket)

    uploaded: list[str] = []
    for local_file in sorted(local_dir.rglob("*")):
        if not local_file.is_file():
            continue
        relative = local_file.relative_to(local_dir)
        s3_key = prefix + relative.as_posix()
        client.upload_file(str(local_file), bucket, s3_key)
        logger.info("[%s] Uploaded %s -> s3://%s/%s", _MODULE, local_file, bucket, s3_key)
        uploaded.append(s3_key)

    if not uploaded:
        raise FileNotFoundError(
            f"[{_MODULE}] No files found to upload in: {local_dir}"
        )

    return uploaded


# -- private helpers ----------------------------------------------------------


def _normalise_prefix(prefix: str) -> str:
    parts = [p for p in prefix.split("/") if p]
    return "/".join(parts) + "/" if parts else ""


def _check_bucket(client, bucket: str) -> None:
    try:
        client.head_bucket(Bucket=bucket)
    except botocore.exceptions.ClientError as exc:
        code = exc.response["Error"]["Code"]
        if code in ("404", "NoSuchBucket"):
            raise FileNotFoundError(
                f"[{_MODULE}] S3 bucket does not exist: {bucket}"
            ) from exc
        raise


def _check_key(client, bucket: str, key: str) -> None:
    try:
        client.head_object(Bucket=bucket, Key=key)
    except botocore.exceptions.ClientError as exc:
        code = exc.response["Error"]["Code"]
        if code in ("404", "NoSuchKey"):
            raise FileNotFoundError(
                f"[{_MODULE}] S3 key does not exist: s3://{bucket}/{key}"
            ) from exc
        raise


def _list_keys(client, bucket: str, prefix: str) -> list[str]:
    keys: list[str] = []
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.endswith("/"):
                keys.append(key)
    return keys
