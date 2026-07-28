resource "aws_s3_bucket" "corpus" { bucket = "${var.project}-${var.env}-corpus" }
resource "aws_s3_bucket_versioning" "corpus" { bucket = aws_s3_bucket.corpus.id; versioning_configuration { status = "Enabled" } }
resource "aws_s3_bucket_server_side_encryption_configuration" "corpus" {
  bucket = aws_s3_bucket.corpus.id
  rule { apply_server_side_encryption_by_default { kms_master_key_id = aws_kms_key.app.arn; sse_algorithm = "aws:kms" } }
}
resource "aws_s3_bucket_public_access_block" "corpus" {
  bucket = aws_s3_bucket.corpus.id; block_public_acls = true; block_public_policy = true
  ignore_public_acls = true; restrict_public_buckets = true
}
