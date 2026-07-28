resource "aws_kms_key" "app" {
  description = "${var.project}-${var.env} app secrets"
  enable_key_rotation = true; deletion_window_in_days = 14
}
resource "aws_kms_alias" "app" { name = "alias/${var.project}-${var.env}"; target_key_id = aws_kms_key.app.key_id }
