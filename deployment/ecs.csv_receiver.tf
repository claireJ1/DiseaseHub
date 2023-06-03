# # #################################################
# # # An example file deploying a container service #
# # #################################################

# # Create a AWS ECS cluster
# # - You should use ${var.group_name} as prefix to prevent naming conflicts
resource "aws_ecs_cluster" "receive_csv" {
  name = "${var.group_name}_${terraform.workspace}_receive_csv_cluster" # TODO: change here
}

# # Define the task so that your cluster can create task instance later
# # - You should use ${var.group_name} as the prefix of the family name
# # - You can alter cpu and memory if you need more, cpu = 256 = 0.25 vCPU and
# #     memory = 512M should be sufficient in general
# # - If you have multiple containers for a task, you can fill them all in
resource "aws_ecs_task_definition" "receive_csv" {
  family                   = "${var.group_name}_${terraform.workspace}_receive_csv_task_def"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  container_definitions = jsonencode([
    {
      name      = "${var.group_name}_${terraform.workspace}_receive_csv" # TODO: change here
      image     = "oak02/unicourse:servercsv_servercsv"                                   # TODO: change here
      essential = true
      portMappings = [
        {
          containerPort = 80 # TODO: change here
          hostPort      = 80 # TODO: change here
          appProtocol   = "http"
          name          = "receive_csv-test-80-tcp" # TODO: change here
        }
      ]
    }
  ])
}

# Fetch available subnets, shouldn't need to change this except the local
#   resource name.
# - var.vpc_id will be injected by the pipeline
data "aws_subnets" "receive_csv" {
  filter {
    name   = "vpc-id"
    values = [var.vpc_id]
  }
}

# Defines a service discovery namespace. Will be useful for service connect
# - You should use ${var.group_name} as the prefix of the name
resource "aws_service_discovery_http_namespace" "receive_csv" {
  name = "${var.group_name}-${terraform.workspace}-discovery-namespace-receive_csv" # TODO: change here
}

# Create a service instance using the task definition above
# - You should use ${var.group_name} as the prefix of the name
# - Usually you only need 1 service, but you may change this if need more
# - the port_name and discovery_name are corresponding to the configuration in
#     aws_ecs_task_definition above
resource "aws_ecs_service" "receive_csv" {
  name            = "${var.group_name}-${terraform.workspace}-receive_csv-ecs-service" # TODO: change here
  cluster         = aws_ecs_cluster.receive_csv.id                           # TODO: change here
  task_definition = aws_ecs_task_definition.receive_csv.arn                  # TODO: change here
  desired_count   = 1                                                      # TODO: change here
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.receive_csv.ids # TODO: change here
    assign_public_ip = true
  }
  service_connect_configuration {
    enabled   = true
    namespace = aws_service_discovery_http_namespace.receive_csv.arn # TODO: change here
    service {
      client_alias {
        port = 80 # TODO: change here
      }
      port_name      = "receive_csv-test-80-tcp" # TODO: change here
      discovery_name = "receive_csv-test-80-tcp" # TODO: change here
    }
  }
}

# Set up a service discovery service
data "aws_service_discovery_service" "receive_csv" {
  name         = "receive_csv-test-80-tcp"                               # TODO: change here
  namespace_id = aws_service_discovery_http_namespace.receive_csv.id # TODO: change here

  depends_on = [
    aws_ecs_service.receive_csv # TODO: change here
  ]
}

# This bridges the route on the gateway and your service.
# - The pipeline will inject var.gateway_api_id
# - integration_method is not the same as the methods in the gateway, it
#     should be ANY here.
# - vpc_connection_id will be injected by the pipeline
resource "aws_apigatewayv2_integration" "receive_csv" {
  api_id             = var.gateway_api_id
  integration_type   = "HTTP_PROXY"
  integration_method = "ANY"
  integration_uri    = data.aws_service_discovery_service.receive_csv.arn # TODO: change here
  connection_type    = "VPC_LINK"
  connection_id      = var.vpc_connection_id

    # since parameters are added through grpc
#   request_parameters = {
#     "overwrite:path" = "/$request.path.subpath" # TODO: change here
#     "token" = 1
#     "name" = 2
#     "data" = 3
#     "data_source" = 4
#     "dataset_type" = 5
#     "event_type" = 6
#   }
}

# This defines the route, linking the integration and the route
# - You may use wildcard in the route key. e.g. POST /${var.group_name}/*
# - You should add /${var.group_name}/ as prefix of your route key to prevent 
#     conflictions in route key
# - You may add parameter in the path. e.g. GET /${var.group_name}/{param}
resource "aws_apigatewayv2_route" "receive_csv" {
  api_id    = var.gateway_api_id
  route_key = "POST /${var.group_name}/ecs/upload_csv"                      # TODO: change here
  target    = "integrations/${aws_apigatewayv2_integration.receive_csv.id}" # TODO: change here
}
