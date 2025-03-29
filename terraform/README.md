# F1 Data Explorer - Terraform

terraform config for f1 data pipeline

## setup

1. init terraform:
   ```bash
   terraform init
   ```

2. check changes:
   ```bash
   terraform plan
   ```

3. apply changes:
   ```bash
   terraform apply
   ```

4. destroy:
   ```bash
   terraform destroy
   ```

## resources

- s3 bucket for raw data
- lambda role with s3 and cloudwatch permissions

## Variables

- `aws_region`: AWS region to deploy resources (default: us-east-1)
- `s3_bucket_name`: Name of the S3 bucket for raw F1 data (default: f1-raw-data)
- `environment`: Environment name (default: dev)

## Outputs

- `s3_bucket_name`: The name of the created S3 bucket
- `s3_bucket_arn`: The ARN of the created S3 bucket
