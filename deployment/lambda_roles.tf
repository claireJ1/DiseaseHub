# Define a role for the lambda function
# - The name must be prefixed with SENG3011_ otherwise AWS will reject it
# - Make sure to proper prefix your role name.
# - You don't need to change assume_role_policy. 
# - You should change managed_policy_arns to be a list of policy ARNs.
# - You can have all your functions using the same role, or create multiple
#     for different functions.
resource "aws_iam_role" "iam_for_lambda" {
  name = "SENG3011_${var.group_name}_${terraform.workspace}_iam_for_lambda"

  assume_role_policy = jsonencode(
    {
      Version = "2012-10-17",
      Statement = [
        {
          Action = "sts:AssumeRole",
          Principal = {
            Service = "lambda.amazonaws.com"
          },
          Effect = "Allow",
          Sid    = ""
        }
      ]
  })
  managed_policy_arns = [
    aws_iam_policy.list_s3_permission.arn,
    aws_iam_policy.put_s3_permission.arn,
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
  ]
}

# Define a new policy allowing your function to access the S3 bucket
# - The name must be prefixed with SENG3011_ otherwise AWS will reject it
# - The more specific, the better. Only ask for permission that your function
#     really need. Be careful with permissions that will result in addition, 
#     modification or deletion of data. This is a way to prevent you from
#     accident or mistakes destroying your work.
resource "aws_iam_policy" "list_s3_permission" {
  name = "SENG3011_${var.group_name}_${terraform.workspace}_list_s3_permission"

  policy = jsonencode(
    {
      "Version" : "2012-10-17",
      "Statement" : [
        {
          "Effect" : "Allow",
          "Action" : "s3:ListBucket",
          "Resource" : ["arn:aws:s3:::${var.global_s3_name}", "arn:aws:s3:::${var.global_s3_name}/*"]
        }
      ]
  })
}

resource "aws_iam_policy" "put_s3_permission" {
  name = "SENG3011_${var.group_name}_${terraform.workspace}_put_s3_permission"

  policy = jsonencode(
    {
      "Version" : "2012-10-17",
      "Statement" : [
        {
          "Effect" : "Allow",
          "Action" : ["s3:PutObject","s3:GetObject"]
          "Resource" : "arn:aws:s3:::${var.global_s3_name}/*"
        }
      ]
  })
}
