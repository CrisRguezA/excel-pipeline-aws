# AWS CLI Deployment Guide · Lambda + S3

This document describes the manual deployment process for the Excel Pipeline Lambda function using AWS CLI.

---

## Prerequisites

- AWS CLI installed and configured (`aws configure`)
- Docker installed (for Linux-compatible packaging)
- Python 3.11
- S3 bucket created

---

## Architecture

```text
S3 (inputs/) -> Lambda (excel-pipeline) -> S3 (outputs/)
                       |
            Lambda Layer (dependencies)
```

---

## Step 1 · Build Lambda Layer

```bash
mkdir lambda_layer
mkdir lambda_layer/python

docker run --rm \
  -v <PROJECT_ROOT>:/var/task \
  -w /var/task \
  public.ecr.aws/sam/build-python3.11:latest \
  pip install pandas==2.2.3 numpy==1.26.4 xlsxwriter==3.2.9 openpyxl==3.1.5 \
  -t /var/task/lambda_layer/python/ --no-cache-dir
```

> numpy pinned to 1.26.4 for Amazon Linux 2 compatibility.
> See decisions_log entry [2026-05-03].

---

## Step 2 · Package Layer

```bash
cd lambda_layer
zip -r ../lambda_layer.zip .
cd ..
```

---

## Step 3 · Package Lambda code

```bash
mkdir build_lambda
cp -r src/excel_pipeline build_lambda/
cd build_lambda
zip -r ../lambda_package.zip .
cd ..
```

---

## Step 4 · Upload to S3

```bash
aws s3 cp lambda_layer.zip s3://<BUCKET>/lambda_layer.zip
aws s3 cp lambda_package.zip s3://<BUCKET>/lambda_package.zip
```

---

## Step 5 · Publish Lambda Layer

```bash
aws lambda publish-layer-version \
  --layer-name excel-pipeline-dependencies \
  --content S3Bucket=<BUCKET>,S3Key=lambda_layer.zip \
  --compatible-runtimes python3.11 \
  --region eu-north-1
```

Note the `LayerVersionArn` from the output.

---

## Step 6 · Create IAM Role

```bash
aws iam create-role \
  --role-name lambda-excel-pipeline-role \
  --assume-role-policy-document file://trust-policy.json

aws iam attach-role-policy \
  --role-name lambda-excel-pipeline-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

aws iam attach-role-policy \
  --role-name lambda-excel-pipeline-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

> For MVP simplicity, `AmazonS3FullAccess` is used. In production, replace it with a least-privilege policy limited to the required bucket and prefixes.

---

## Step 7 · Create Lambda Function

```bash
aws lambda create-function \
  --function-name excel-pipeline \
  --runtime python3.11 \
  --role arn:aws:iam::<ACCOUNT_ID>:role/lambda-excel-pipeline-role \
  --handler excel_pipeline.cloud.lambda_handler.lambda_handler \
  --code S3Bucket=<BUCKET>,S3Key=lambda_package.zip \
  --timeout 60 \
  --memory-size 512 \
  --layers <LAYER_ARN> \
  --region eu-north-1
```

> If the function already exists, use `update-function-code` instead of `create-function`.

---

## Step 8 · Upload input files

```bash
aws s3 cp data/raw/ s3://<BUCKET>/inputs/ --recursive
aws s3 cp configs/wood_sales_config.json s3://<BUCKET>/configs/wood_sales_config.json
```

---

## Step 9 · Invoke Lambda

Create `event.json`:

```json
{
  "bucket": "<BUCKET>",
  "input_prefix": "inputs/",
  "output_prefix": "outputs/",
  "config_key": "configs/wood_sales_config.json"
}
```

Invoke:

```bash
aws lambda invoke \
  --function-name excel-pipeline \
  --payload file://event.json \
  --cli-binary-format raw-in-base64-out \
  response.json \
  --region eu-north-1

cat response.json
```

---

## Step 10 · Download outputs

```bash
aws s3 ls s3://<BUCKET>/outputs/ --region eu-north-1
aws s3 cp s3://<BUCKET>/outputs/ data/outputs/ --recursive
```

---

## Updating the function

After code changes:

```bash
aws s3 cp lambda_package.zip s3://<BUCKET>/lambda_package.zip

aws lambda update-function-code \
  --function-name excel-pipeline \
  --s3-bucket <BUCKET> \
  --s3-key lambda_package.zip \
  --region eu-north-1
```

---

## Notes

- `<BUCKET>` = your S3 bucket name
- `<ACCOUNT_ID>` = your AWS account ID
- `<LAYER_ARN>` = full ARN from publish-layer-version output
- `boto3` is excluded from packaging - already available in Lambda runtime
- `build_lambda/`, `lambda_layer/`, `*.zip` are excluded from git via `.gitignore`