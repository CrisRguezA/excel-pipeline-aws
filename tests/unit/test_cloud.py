"""Tests for cloud.s3_io and cloud.lambda_handler -- mocked S3, no real AWS."""

from __future__ import annotations

from unittest.mock import patch

import boto3
import pytest
from moto import mock_aws

from excel_pipeline.cloud.lambda_handler import lambda_handler
from excel_pipeline.cloud.s3_io import (
    download_s3_file,
    download_s3_prefix,
    upload_directory,
)

_BUCKET = "test-bucket"
_REGION = "us-east-1"


@pytest.fixture(autouse=True)
def aws_credentials(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID",     "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN",    "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN",     "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION",    _REGION)


@pytest.fixture()
def s3_bucket():
    with mock_aws():
        client = boto3.client("s3", region_name=_REGION)
        client.create_bucket(Bucket=_BUCKET)
        yield client


class TestS3IO:
    def test_download_s3_prefix(self, s3_bucket, tmp_path):
        s3_bucket.put_object(Bucket=_BUCKET, Key="inputs/a.xlsx",     Body=b"aa")
        s3_bucket.put_object(Bucket=_BUCKET, Key="inputs/sub/b.xlsx", Body=b"bb")

        paths = download_s3_prefix(_BUCKET, "inputs/", tmp_path)

        assert (tmp_path / "a.xlsx").exists()
        assert (tmp_path / "sub" / "b.xlsx").exists()
        assert len(paths) == 2

    def test_download_s3_file(self, s3_bucket, tmp_path):
        s3_bucket.put_object(
            Bucket=_BUCKET, Key="configs/config.json", Body=b'{"k":"v"}'
        )
        local_path = tmp_path / "config.json"

        result = download_s3_file(_BUCKET, "configs/config.json", local_path)

        assert result == local_path
        assert local_path.read_bytes() == b'{"k":"v"}'

    def test_upload_directory(self, s3_bucket, tmp_path):
        (tmp_path / "report.xlsx").write_bytes(b"report")
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "log.json").write_bytes(b"log")

        keys = upload_directory(_BUCKET, "outputs/", tmp_path)

        assert "outputs/report.xlsx"  in keys
        assert "outputs/sub/log.json" in keys
        s3_bucket.head_object(Bucket=_BUCKET, Key="outputs/report.xlsx")
        s3_bucket.head_object(Bucket=_BUCKET, Key="outputs/sub/log.json")


class TestLambdaHandler:
    _EVENT = {
        "bucket":        _BUCKET,
        "input_prefix":  "inputs/",
        "output_prefix": "outputs/",
        "config_key":    "configs/config.json",
    }

    def test_success(self, s3_bucket, tmp_path):
        s3_bucket.put_object(Bucket=_BUCKET, Key="inputs/data.xlsx",    Body=b"x")
        s3_bucket.put_object(Bucket=_BUCKET, Key="configs/config.json", Body=b"{}")

        tmp_inputs  = tmp_path / "inputs"
        tmp_outputs = tmp_path / "outputs"
        tmp_config  = tmp_path / "config.json"
        fake_summary = {"rows_in": 10, "rows_out": 8}

        def fake_run(input_path, output_path, config_path):
            output_path.mkdir(parents=True, exist_ok=True)
            (output_path / "report.xlsx").write_bytes(b"report")
            return fake_summary

        with (
            patch("excel_pipeline.cloud.lambda_handler._TMP_INPUTS",  tmp_inputs),
            patch("excel_pipeline.cloud.lambda_handler._TMP_OUTPUTS", tmp_outputs),
            patch("excel_pipeline.cloud.lambda_handler._TMP_CONFIG",  tmp_config),
            patch(
                "excel_pipeline.cloud.lambda_handler.run_pipeline",
                side_effect=fake_run,
            ),
        ):
            response = lambda_handler(self._EVENT, context=None)

        assert response["status"]        == "success"
        assert response["summary"]       == fake_summary
        assert "outputs/report.xlsx" in response["uploaded_keys"]
        s3_bucket.head_object(Bucket=_BUCKET, Key="outputs/report.xlsx")

    def test_missing_key_returns_error(self):
        response = lambda_handler({"bucket": _BUCKET}, context=None)

        assert response["status"]     == "error"
        assert response["error_type"] == "ValueError"
        assert "Missing required event keys" in response["error_message"]
