terraform {
  required_version = ">= 1.6"
  required_providers { aws = { source = "hashicorp/aws", version = ">= 5.40" } }
  backend "s3" {
    bucket = "your-tf-state-bucket"; key = "cognita/terraform.tfstate"
    region = "us-east-1"; dynamodb_table = "tf-locks"; encrypt = true
  }
}
provider "aws" {
  region = var.region
  default_tags { tags = { Project = "cognita", Env = var.env, ManagedBy = "terraform" } }
}
