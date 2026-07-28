resource "aws_iam_role" "app" {
  name = "${var.project}-${var.env}-app"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = var.eks_oidc_provider_arn != "" ? [{
      Effect = "Allow"; Principal = { Federated = var.eks_oidc_provider_arn }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = { StringEquals = { "${replace(var.eks_oidc_provider_arn, "/^.*provider\\//", "")}:sub" = "system:serviceaccount:${var.eks_namespace}:${var.eks_sa_name}" } }
    }] : [{ Effect = "Allow"; Principal = { Service = "ecs-tasks.amazonaws.com" }; Action = "sts:AssumeRole" }]
  })
}
resource "aws_iam_role_policy" "secrets" {
  role = aws_iam_role.app.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [
    { Effect = "Allow", Action = ["secretsmanager:GetSecretValue"], Resource = ["${aws_secretsmanager_secret.bundle.arn}*"] },
    { Effect = "Allow", Action = ["kms:Decrypt", "kms:GenerateDataKey"], Resource = [aws_kms_key.app.arn] },
  ] })
}
resource "aws_iam_role_policy" "corpus" {
  role = aws_iam_role.app.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [{
    Effect = "Allow", Action = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
    Resource = [aws_s3_bucket.corpus.arn, "${aws_s3_bucket.corpus.arn}/*"] }] })
}
output "app_role_arn" { value = aws_iam_role.app.arn }
