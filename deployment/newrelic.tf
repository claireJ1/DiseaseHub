resource "aws_iam_role" "iam_for_new_relic" {
  name = "SENG3011_${var.group_name}_${terraform.workspace}_iam_for_new_relic"

  assume_role_policy = jsonencode(
    {
      Version = "2012-10-17",
      Statement = [
        {
          Action = "sts:AssumeRole",
          Principal = {
            AWS = "arn:aws:iam::754728514883:root"
          },
          Effect = "Allow",
          Condition = {
            StringEquals = {
              "sts:ExternalId"= "3858862" # TODO: CHANGE THIS TO YOUR NEW RELIC ID
            }
          }
        }
      ]
  })
  managed_policy_arns = [
    "arn:aws:iam::aws:policy/ReadOnlyAccess",
  ]
}

output "iam_for_new_relic_arn" {
  value = aws_iam_role.iam_for_new_relic.arn
}