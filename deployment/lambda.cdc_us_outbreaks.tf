###############################################
# An example file deploying a lambda function #
###############################################

# Tells Terraform to run build.sh when any of these file below changed
# - path.module is the location of this .tf file
resource "null_resource" "build_cdc_us_scrape" {
  triggers = {
    always_run = "${timestamp()}"
  }

  provisioner "local-exec" {
    command = "bash ${path.module}/../code/cdc_us_scrape/build.sh"
  }
}


# Tells Terraform to compress your source code with dependencies
data "archive_file" "cdc_us_scrape" {
  type        = "zip"
  output_path = "${path.module}/../code/cdc_us_scrape.zip"
  source_dir  = "${path.module}/../code/cdc_us_scrape"

  depends_on = [
    null_resource.build_cdc_us_scrape
  ]
}

# Tells Terraform to create an AWS lambda function
# - Filename here corresponds to the output_path in archive_file.hello_world.
# - Pipeline will inject the content of .GROUP_NAME to be var.group_name, you
#     should use it as a prefix in your function_name to prevent conflictions.
# - Use terraform.workspace to distinguish functions in different stages. It'll
#     be injected by the pipeline when you manually run it.
# - You should set source_code_hash so that after your code changed, Terraform
#     can redeploy your function.
# - You can inject environment variables to your lambda function
resource "aws_lambda_function" "cdc_us_scrape" {
  filename      = data.archive_file.cdc_us_scrape.output_path
  function_name = "${var.group_name}_${terraform.workspace}_cdc_us_scrape"
  handler       = "handler.handler"
  runtime       = "python3.9" # TODO: change here

  role             = aws_iam_role.iam_for_lambda.arn
  source_code_hash = data.archive_file.cdc_us_scrape.output_base64sha256

  environment {
    variables = {
      ENV            = "${terraform.workspace}"
      GLOBAL_S3_NAME = "${var.global_s3_name}"

      # For the instrumentation handler to invoke your real handler, we need this value
      NEW_RELIC_LAMBDA_HANDLER = "handler.handler"
      NEW_RELIC_ACCOUNT_ID     = "05464b8e-3f03-4280-a3a0-1a3d758d1336"
      NEW_RELIC_LICENSE_KEY    = "3028D48626EB5662CB8B44B08156DF7C9846428436AA6C9F2F25EA8491BE3F13"
      # Enable NR Lambda extension if the telemetry data are ingested via lambda extension
      NEW_RELIC_LAMBDA_EXTENSION_ENABLED = true
      # Enable Distributed tracing for in-depth monitoring of transactions in lambda (Optional)
      NEW_RELIC_DISTRIBUTED_TRACING_ENABLED = true
    }
  }
  # This layer includes the New Relic Lambda Extension, a sidecar process that sends telemetry,
  # as well as the New Relic Agent, and a handler wrapper that makes integration easy.
  layers = ["arn:aws:lambda:ap-southeast-2:451483290750:layer:NewRelicPython39:40" ]

  timeout = 150
}

# Work as a template
# - For schedule_expression, see https://docs.aws.amazon.com/lambda/latest/dg/services-cloudwatchevents-expressions.html
#     This example creates a scheduled function being invoked every 12 hours
resource "aws_cloudwatch_event_rule" "cdc_us_scrape" {
  name                = "${var.group_name}_${terraform.workspace}_cdc_us_scrape" # TODO: change here
  description         = "Schedule for Lambda Function"                       # TODO: change here
  schedule_expression = "rate(7 days)"                               # TODO: change here
}

resource "aws_cloudwatch_event_target" "cdc_us_scrape" {
  rule      = aws_cloudwatch_event_rule.cdc_us_scrape.name
  target_id = "${var.group_name}_${terraform.workspace}_cdc_us_scrape" # TODO: change here
  arn       = aws_lambda_function.cdc_us_scrape.arn                    # TODO: change here
}

# Allows your function to be invoked by the Event Bridge.
resource "aws_lambda_permission" "cdc_us_scrape" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cdc_us_scrape.function_name # TODO: change here
  principal     = "events.amazonaws.com"
}

# Including this resource will keep a log as your function being called
resource "aws_cloudwatch_log_group" "cdc_us_scrape_log" {
  name              = "/aws/lambda/${aws_lambda_function.cdc_us_scrape.function_name}" # TODO: change here
  retention_in_days = 0
  lifecycle {
    prevent_destroy = false
  }
}
