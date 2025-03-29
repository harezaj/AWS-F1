output "s3_bucket_name" {
  description = "The name of the S3 bucket"
  value       = aws_s3_bucket.f1_raw_data.id
}

output "s3_bucket_arn" {
  description = "The ARN of the S3 bucket"
  value       = aws_s3_bucket.f1_raw_data.arn
}

output "lambda_role_arn" {
  description = "The ARN of the Lambda IAM role"
  value       = aws_iam_role.lambda_role.arn
}
