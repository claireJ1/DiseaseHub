###############################################
# An example file deploying a lambda function #
###############################################

# Tells Terraform to run build.sh when any of these file below changed
# - path.module is the location of this .tf file
resource "null_resource" "upload_global_incident" {
  triggers = {
    always_run = "${timestamp()}"
  }

  provisioner "local-exec" {
    command = "bash ${path.module}/../code/upload_global_incident/build.sh"
  }
}


# Tells Terraform to compress your source code with dependencies
data "archive_file" "upload_global_incident" {
  type        = "zip"
  output_path = "${path.module}/../code/upload_global_incident.zip" # TODO: change here
  source_dir  = "${path.module}/../code/upload_global_incident"     # TODO: change here

  depends_on = [
    null_resource.upload_global_incident # TODO: change here
  ]
}

# Tells Terraform to create an AWS lambda function
# - Filename here corresponds to the output_path in archive_file.scheduled.
# - Pipeline will inject the content of .GROUP_NAME to be var.group_name, you
#     should use it as a prefix in your function_name to prevent conflictions.
# - You should set source_code_hash so that after your code changed, Terraform
#     can redeploy your function.
resource "aws_lambda_function" "upload_global_incident" {
  filename      = data.archive_file.upload_global_incident.output_path
  function_name = "${var.group_name}_${terraform.workspace}_upload_global_incident" # TODO: change here
  handler       = "handler.handler"
  runtime       = "python3.9" # TODO: change here

  role             = aws_iam_role.iam_for_lambda.arn
  source_code_hash = data.archive_file.upload_global_incident.output_base64sha256 # TODO: change here

  environment {
    variables = {
      ENV            = "${terraform.workspace}"
      GLOBAL_S3_NAME = "${var.global_s3_name}"
    }
  }
  timeout = 150
}

# Work as a template
# - For schedule_expression, see https://docs.aws.amazon.com/lambda/latest/dg/services-cloudwatchevents-expressions.html
#     This example creates a scheduled function being invoked every 12 hours
resource "aws_cloudwatch_event_rule" "upload_global_incident" {
  name                = "${var.group_name}_${terraform.workspace}_upload_global_incident" # TODO: change here
  description         = "Schedule for Lambda Function"                       # TODO: change here
  schedule_expression = "rate(7 days)"                               # TODO: change here
}

resource "aws_cloudwatch_event_target" "upload_global_incident" {
  rule      = aws_cloudwatch_event_rule.upload_global_incident.name
  target_id = "${var.group_name}_${terraform.workspace}_upload_global_incident" # TODO: change here
  arn       = aws_lambda_function.upload_global_incident.arn                    # TODO: change here
}

# Allows your function to be invoked by the Event Bridge.
resource "aws_lambda_permission" "upload_global_incident" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.upload_global_incident.function_name # TODO: change here
  principal     = "events.amazonaws.com"
}

# Including this resource will keep a log as your function being called
resource "aws_cloudwatch_log_group" "upload_global_incident_log" {
  name              = "/aws/lambda/${aws_lambda_function.upload_global_incident.function_name}" # TODO: change here
  retention_in_days = 7
  lifecycle {
    prevent_destroy = false
  }
}
