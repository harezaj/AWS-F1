terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# S3 bucket for raw F1 data
resource "aws_s3_bucket" "f1_raw_data" {
  bucket = var.s3_bucket_name

  tags = {
    Name        = var.s3_bucket_name
    Environment = var.environment
  }
}

# Prevent accidental deletion of this S3 bucket
resource "aws_s3_bucket_lifecycle_configuration" "f1_raw_data" {
  bucket = aws_s3_bucket.f1_raw_data.id

  rule {
    id     = "cleanup"
    status = "Enabled"

    expiration {
      days = 7  # Keep raw data for 7 days
    }
  }
}

# Enable versioning for the S3 bucket
resource "aws_s3_bucket_versioning" "f1_raw_data" {
  bucket = aws_s3_bucket.f1_raw_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Block public access to the S3 bucket
resource "aws_s3_bucket_public_access_block" "f1_raw_data" {
  bucket = aws_s3_bucket.f1_raw_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
