# # #################################################
# # # An example file deploying a container service #
# # #################################################

# # Create a AWS ECS cluster
# # - You should use ${var.group_name} as prefix to prevent naming conflicts
resource "aws_ecs_cluster" "cdc_int_ecs" {
    name = "${var.group_name}_${terraform.workspace}_cdc_int_ecs_cluster" # TODO: change here
}

# # Define the task so that your cluster can create task instance later
# # - You should use ${var.group_name} as the prefix of the family name
# # - You can alter cpu and memory if you need more, cpu = 256 = 0.25 vCPU and
# #     memory = 512M should be sufficient in general
# # - If you have multiple containers for a task, you can fill them all in
resource "aws_ecs_task_definition" "cdc_int_ecs" {
    family                   = "${var.group_name}_${terraform.workspace}_cdc_int_ecs_task_def"
    network_mode             = "awsvpc"
    requires_compatibilities = ["FARGATE"]
    cpu                      = 1024
    memory                   = 2048
    task_role_arn            = aws_iam_role.iam_for_ecs.arn
    execution_role_arn       = aws_iam_role.iam_for_ecs.arn

    container_definitions = jsonencode([
      {
        name      = "${var.group_name}_${terraform.workspace}_cdc_int_ecs" # TODO: change here
        image     = "goneami/h14bbravo:latest"                                   # TODO: change here
        essential = true
        portMappings = [
          {
            containerPort = 80 # TODO: change here
            hostPort      = 80 # TODO: change here
            appProtocol   = "http"
            name          = "cdc_int_ecs-test-80-tcp" # TODO: change here
          }
        ],
        "logConfiguration": {
          "logDriver": "awslogs",
          "options": {
              "awslogs-create-group": "true",
              "awslogs-group": "/aws/ecs/${var.group_name}_${terraform.workspace}_cdc_int",
              "awslogs-region": "ap-southeast-2",
              "awslogs-stream-prefix": "H14B-Bravo"
          }
        }
        environment = [
        {
          name = "GLOBAL_S3_NAME"
          value = "${var.global_s3_name}"
        }
      ]
      },
      {
        name      = "${var.group_name}_${terraform.workspace}_cdc_us_ecs" # TODO: change here
        image     = "goneami/cdcuscontainer:latest"                                   # TODO: change here
        essential = true
        portMappings = [
          {
            containerPort = 443 # TODO: change here
            hostPort      = 443 # TODO: change here
            appProtocol   = "http"
            name          = "cdc_us_ecs-test-80-tcp" # TODO: change here
          }
        ],
        "logConfiguration": {
          "logDriver": "awslogs",
          "options": {
              "awslogs-create-group": "true",
              "awslogs-group": "/aws/ecs/${var.group_name}_${terraform.workspace}_cdc_us",
              "awslogs-region": "ap-southeast-2",
              "awslogs-stream-prefix": "H14B-Bravo"
          }
        }
        environment = [
        {
          name = "GLOBAL_S3_NAME"
          value = "${var.global_s3_name}"
        }
      ] 
      }
    ])
}

# # Fetch available subnets, shouldn't need to change this except the local
# #   resource name.
# # - var.vpc_id will be injected by the pipeline
  data "aws_subnets" "cdc_int_ecs" {
    filter {
      name   = "vpc-id"
      values = [var.vpc_id]
    }
  }

# # Defines a service discovery namespace. Will be useful for service connect
# # - You should use ${var.group_name} as the prefix of the name
  resource "aws_service_discovery_http_namespace" "cdc_int_ecs" {
    name = "${var.group_name}-${terraform.workspace}-discovery-namespace-cdc_int_ecs" # TODO: change here
  }

# # Create a service instance using the task definition above
# # - You should use ${var.group_name} as the prefix of the name
# # - Usually you only need 1 service, but you may change this if need more
# # - the port_name and discovery_name are corresponding to the configuration in
# #     aws_ecs_task_definition above
  resource "aws_ecs_service" "cdc_int_ecs" {
    name            = "${var.group_name}-${terraform.workspace}-cdc_int_ecs-service" # TODO: change here
    cluster         = aws_ecs_cluster.cdc_int_ecs.id                           # TODO: change here
    task_definition = aws_ecs_task_definition.cdc_int_ecs.arn                  # TODO: change here
    desired_count   = 1                                                      # TODO: change here
    launch_type     = "FARGATE"

    network_configuration {
      subnets          = data.aws_subnets.cdc_int_ecs.ids # TODO: change here
      assign_public_ip = true
    }
    service_connect_configuration {
      enabled   = true
      namespace = aws_service_discovery_http_namespace.cdc_int_ecs.arn # TODO: change here
      service {
        client_alias {
          port = 80 # TODO: change here
        }
        port_name      = "cdc_int_ecs-test-80-tcp" # TODO: change here
        discovery_name = "cdc_int_ecs-test-80-tcp" # TODO: change here
      }
    }
  }

# # Set up a service discovery service
  data "aws_service_discovery_service" "cdc_int_ecs" {
    name         = "cdc_int_ecs-test-80-tcp"                               # TODO: change here
    namespace_id = aws_service_discovery_http_namespace.cdc_int_ecs.id # TODO: change here

    depends_on = [
      aws_ecs_service.cdc_int_ecs # TODO: change here
    ]
  }

# # This bridges the route on the gateway and your service.
# # - The pipeline will inject var.gateway_api_id
# # - integration_method is not the same as the methods in the gateway, it
# #     should be ANY here.
# # - vpc_connection_id will be injected by the pipeline
  resource "aws_apigatewayv2_integration" "cdc_int_ecs" {
    api_id             = var.gateway_api_id
    integration_type   = "HTTP_PROXY"
    integration_method = "ANY"
    integration_uri    = data.aws_service_discovery_service.cdc_int_ecs.arn # TODO: change here
    connection_type    = "VPC_LINK"
    connection_id      = var.vpc_connection_id

    request_parameters = {
      "overwrite:path" = "/$request.path.subpath" # TODO: change here
    }
  }

# # This defines the route, linking the integration and the route
# # - You may use wildcard in the route key. e.g. POST /${var.group_name}/*
# # - You should add /${var.group_name}/ as prefix of your route key to prevent 
# #     conflictions in route key
# # - You may add parameter in the path. e.g. GET /${var.group_name}/{param}
  resource "aws_apigatewayv2_route" "cdc_int_ecs" {
    api_id    = var.gateway_api_id
    route_key = "ANY /${var.group_name}/ecs/cdc_int_ecs"                      # TODO: change here
    target    = "integrations/${aws_apigatewayv2_integration.cdc_int_ecs.id}" # TODO: change here
  }

# Including this resource will keep a log as your function being called
resource "aws_cloudwatch_log_group" "cdc_int_ecs" {
  name              = "/aws/ecs/${var.group_name}_${terraform.workspace}_cdc_int"
  retention_in_days = 7
  lifecycle {
    prevent_destroy = false
  }
}

resource "aws_cloudwatch_event_rule" "cdc_web_scrape" {
  name        = "${var.group_name}${terraform.workspace}cdc_scrape_ecs_event_rule"
  description = "CDC scraping"
  schedule_expression = "rate(7 days)"
}

