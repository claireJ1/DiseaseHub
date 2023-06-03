output "api_endpoint" {
  value = data.aws_apigatewayv2_api.api_gateway_global.api_endpoint
}

output "hello_world" {
  value = aws_apigatewayv2_route.hello_world.route_key
}

output "list_s3" {
  value = aws_apigatewayv2_route.list_s3.route_key
}
