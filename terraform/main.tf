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

# Create a bucket to store raw F1 data
resource "aws_s3_bucket" "f1_raw_data" {
  bucket = var.s3_bucket_name

  tags = {
    Name        = var.s3_bucket_name
    Environment = var.environment
  }
}

# Enable default encryption for the S3 bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "f1_raw_data" {
  bucket = aws_s3_bucket.f1_raw_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Clean up old data after 1 day to keep things tidy
resource "aws_s3_bucket_lifecycle_configuration" "f1_raw_data" {
  bucket = aws_s3_bucket.f1_raw_data.id

  rule {
    id     = "cleanup"
    status = "Enabled"

    filter {
      prefix = "raw/"
    }

    expiration {
      days = 1
    }
  }
}

# Keep track of file versions in case we need to roll back
resource "aws_s3_bucket_versioning" "f1_raw_data" {
  bucket = aws_s3_bucket.f1_raw_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Lock down the bucket - no public access allowed
resource "aws_s3_bucket_public_access_block" "f1_raw_data" {
  bucket = aws_s3_bucket.f1_raw_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Set up a role for Lambda functions
resource "aws_iam_role" "lambda_role" {
  name = "f1-data-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "f1-data-lambda-role"
    Environment = var.environment
  }
}

# Give Lambda functions permission to work with S3 and CloudWatch
resource "aws_iam_role_policy" "lambda_policy" {
  name = "f1-data-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
          "s3:DeleteObject"
        ]
        Resource = [
          aws_s3_bucket.f1_raw_data.arn,
          "${aws_s3_bucket.f1_raw_data.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:*:log-group:/aws/lambda/f1-data-*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:*:log-group:/aws/lambda/f1-data-*:log-stream:*"
      }
    ]
  })
}

# Add the basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Create Secrets Manager secret for Supabase credentials
resource "aws_secretsmanager_secret" "supabase_credentials" {
  name        = "f1-data-supabase-credentials"
  description = "Credentials for Supabase database connection"
  
  tags = {
    Name        = "f1-data-supabase-credentials"
    Environment = var.environment
  }
}

# Policy to allow Lambda to access the secret
resource "aws_iam_policy" "secrets_manager_access" {
  name        = "f1-data-secrets-manager-access"
  description = "Allow access to Supabase credentials in Secrets Manager"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
        ]
        Resource = [
          aws_secretsmanager_secret.supabase_credentials.arn
        ]
      }
    ]
  })
}

# Attach the Secrets Manager policy to the Lambda role
resource "aws_iam_role_policy_attachment" "lambda_secrets_manager" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.secrets_manager_access.arn
}

# Create Lambda function to fetch F1 data
resource "aws_lambda_function" "f1_data_fetcher" {
  filename         = "../lambda/data_fetcher/function.zip"
  function_name    = "f1-data-fetcher"
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.9"
  timeout         = 300  # Give it 5 minutes to run
  memory_size     = 256
  source_code_hash = filebase64sha256("../lambda/data_fetcher/function.zip")

  environment {
    variables = {
      S3_BUCKET_NAME = aws_s3_bucket.f1_raw_data.id
    }
  }

  tags = {
    Name        = "f1-data-fetcher"
    Environment = var.environment
  }
}

# Create EventBridge rule to trigger Lambda daily
resource "aws_cloudwatch_event_rule" "f1_data_fetch" {
  name                = "f1-data-fetch"
  description         = "Trigger F1 data fetch Lambda daily"
  schedule_expression = "rate(1 day)"
  state              = "ENABLED"

  tags = {
    Name        = "f1-data-fetch"
    Environment = var.environment
  }
}

# Allow EventBridge to invoke Lambda
resource "aws_cloudwatch_event_target" "f1_data_fetch" {
  rule      = aws_cloudwatch_event_rule.f1_data_fetch.name
  target_id = "F1DataFetch"
  arn       = aws_lambda_function.f1_data_fetcher.arn
}

# Allow EventBridge to invoke Lambda
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.f1_data_fetcher.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.f1_data_fetch.arn
}

# Create Lambda function for data loading
resource "aws_lambda_function" "f1_data_loader" {
  filename         = "../lambda/data_loader/function.zip"
  function_name    = "f1-data-loader"
  role            = aws_iam_role.lambda_role.arn
  handler         = "loader_function.lambda_handler"
  runtime         = "python3.9"
  timeout         = 300
  memory_size     = 512
  source_code_hash = filebase64sha256("../lambda/data_loader/function.zip")

  environment {
    variables = {
      S3_BUCKET_NAME = aws_s3_bucket.f1_raw_data.id
      SUPABASE_SECRET_NAME = aws_secretsmanager_secret.supabase_credentials.name
    }
  }

  tags = {
    Name        = "f1-data-loader"
    Environment = var.environment
  }
}
