terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
  backend "s3" {
    # Intentially leave empty, will be filled by the pipeline
  }
}

provider "aws" {
  region = "ap-southeast-2"
}
