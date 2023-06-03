variable "group_name" {
  type     = string
  nullable = false
  default  = ""
}

variable "global_s3_name" {
  type     = string
  nullable = false
  default  = ""
}

variable "gateway_api_id" {
  type     = string
  nullable = false
  default  = ""
}

variable "gateway_auth_id" {
  type     = string
  nullable = false
  default  = ""
}

variable "vpc_id" {
  type     = string
  nullable = false
  default  = ""
}

variable "vpc_connection_id" {
  type     = string
  nullable = false
  default  = ""
}

# Observability variables

variable "aws_region" {
  type = string
  default  = ""
}

variable "lambda_function_handler" {
  type = string
  default  = ""
}

variable "lambda_function_name" {
  type = string
  default  = ""
}

variable "wrapper_handler" {
  type = string
  default  = ""
}

variable "lambda_runtime" {
  type = string
  default  = ""
}

variable "lambda_zip_filename" {
  type = string
  default  = ""
}

variable "newrelic_account_id" {
  type = string
  default  = ""
}

variable "newrelic_layer" {
  type = string
  default  = ""
}

# ECS Container Variables

variable "ecs_container_stop_timeout" {
  description = "Time duration to wait from when a task is stopped before its containers are forcefully killed if they do not exit normally on their own."
  default     = "180s"
  type        = string
}
