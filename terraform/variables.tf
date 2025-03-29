variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "s3_bucket_name" {
  type    = string
  default = "f1-raw-data-794431322648"
}

variable "environment" {
  type    = string
  default = "dev"
}
