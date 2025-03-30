output "s3_bucket_name" {
  value = aws_s3_bucket.f1_raw_data.id
}

output "s3_bucket_arn" {
  value = aws_s3_bucket.f1_raw_data.arn
}

output "lambda_role_arn" {
  value = aws_iam_role.lambda_role.arn
}

output "lambda_function_arn" {
  value = aws_lambda_function.f1_data_fetcher.arn
}
