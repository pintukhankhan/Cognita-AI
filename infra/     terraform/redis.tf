resource "aws_elasticache_subnet_group" "app" { name = "${var.project}-${var.env}"; subnet_ids = var.redis_subnet_ids }
resource "aws_elasticache_serverless_cache" "app" {
  engine = "redis"; serverless_cache_name = "${var.project}-${var.env}"
  subnet_group_name = aws_elasticache_subnet_group.app.name
  security_group_ids = [aws_security_group.redis.id]; kms_key_id = aws_kms_key.app.arn
  snapshot_retention_limit = 7
  cache_usage_limits { data_storage { maximum = 10, unit = "GB" }; ecpu_per_second { maximum = 1000 } }
}
resource "aws_security_group" "redis" { name = "${var.project}-${var.env}-redis"; vpc_id = var.vpc_id }
resource "aws_security_group_rule" "redis_in" {
  type = "ingress"; from_port = 6379; to_port = 6379; protocol = "tcp"
  security_group_id = aws_security_group.redis.id; source_security_group_id = var.app_security_group_id
}
output "redis_url" { value = "rediss://${aws_elasticache_serverless_cache.app.endpoint.0.address}:6379/0"; sensitive = true }
