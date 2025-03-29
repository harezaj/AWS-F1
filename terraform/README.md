# F1 Data Explorer - Terraform Configuration

This directory contains the Terraform configuration for the F1 Data Explorer project's AWS infrastructure.

## Prerequisites

- AWS CLI installed and configured
- Terraform installed
- AWS credentials with appropriate permissions

## Resources Created

- S3 bucket for storing raw F1 data
- S3 bucket lifecycle rules for data cleanup
- S3 bucket versioning
- S3 bucket public access blocking

## Usage

1. Initialize Terraform:
   ```bash
   terraform init
   ```

2. Review the planned changes:
   ```bash
   terraform plan
   ```

3. Apply the configuration:
   ```bash
   terraform apply
   ```

4. To destroy the infrastructure:
   ```bash
   terraform destroy
   ```

## Variables

- `aws_region`: AWS region to deploy resources (default: us-east-1)
- `s3_bucket_name`: Name of the S3 bucket for raw F1 data (default: f1-raw-data)
- `environment`: Environment name (default: dev)

## Outputs

- `s3_bucket_name`: The name of the created S3 bucket
- `s3_bucket_arn`: The ARN of the created S3 bucket
