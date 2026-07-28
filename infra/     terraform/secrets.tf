locals {
  secrets = {
    OPENAI_API_KEY = var.openai_api_key, PINECONE_API_KEY = var.pinecone_api_key,
    NEO4J_URI = var.neo4j_uri, NEO4J_USER = var.neo4j_user, NEO4J_PASSWORD = var.neo4j_password,
    SECRET_KEY = var.secret_key,
  }
}
resource "aws_secretsmanager_secret" "app" {
  for_each = local.secrets; name = "${var.project}/${var.env}/${each.key}"
  kms_key_id = aws_kms_key.app.arn; recovery_window_in_days = 7
}
resource "aws_secretsmanager_secret_version" "app" {
  for_each = local.secrets; secret_id = aws_secretsmanager_secret.app[each.key].id; secret_string = each.value
}
resource "aws_secretsmanager_secret" "bundle" { name = "${var.project}/${var.env}/env-bundle"; kms_key_id = aws_kms_key.app.arn }
resource "aws_secretsmanager_secret_version" "bundle" {
  secret_id = aws_secretsmanager_secret.bundle.id; secret_string = jsonencode(local.secrets)
}
