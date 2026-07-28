variable "region"  { default = "us-east-1" }
variable "env"     { default = "production" }
variable "project" { default = "cognita" }
variable "eks_oidc_provider_arn" { default = "" }
variable "eks_namespace" { default = "production" }
variable "eks_sa_name"   { default = "cognita" }
variable "vpc_id"                 { type = string }
variable "redis_subnet_ids"       { type = list(string) }
variable "app_security_group_id"  { type = string }
variable "openai_api_key"   { type = string, sensitive = true }
variable "pinecone_api_key" { type = string, sensitive = true }
variable "neo4j_uri"        { type = string }
variable "neo4j_user"       { type = string, default = "neo4j" }
variable "neo4j_password"   { type = string, sensitive = true }
variable "secret_key"       { type = string, sensitive = true }
