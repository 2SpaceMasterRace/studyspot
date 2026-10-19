# The static frontend bucket.
#
# The bucket is private. CloudFront reads it through an origin access control, so
# the only way to the objects is the distribution, and `bun run build` output can
# be synced straight here.

resource "aws_s3_bucket" "site" {
  # The account ID keeps the name globally unique without a random suffix that
  # would change the bucket on every rebuild.
  bucket        = "${local.name_prefix}-site-${data.aws_caller_identity.current.account_id}"
  force_destroy = var.site_bucket_force_destroy

  tags = {
    Name = "${local.name_prefix}-site"
  }
}

resource "aws_s3_bucket_public_access_block" "site" {
  bucket = aws_s3_bucket.site.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "site" {
  bucket = aws_s3_bucket.site.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "site" {
  bucket = aws_s3_bucket.site.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# The build output is reproducible from the repository, so versioning is off: it
# would only accumulate storage for artifacts a rebuild can recreate.
resource "aws_s3_bucket_versioning" "site" {
  bucket = aws_s3_bucket.site.id

  versioning_configuration {
    status = "Disabled"
  }
}

data "aws_iam_policy_document" "site" {
  statement {
    sid     = "AllowCloudFrontRead"
    effect  = "Allow"
    actions = ["s3:GetObject"]

    resources = ["${aws_s3_bucket.site.arn}/*"]

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    # Without this condition the policy would let any CloudFront distribution in
    # any account read the bucket.
    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.main.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "site" {
  bucket = aws_s3_bucket.site.id
  policy = data.aws_iam_policy_document.site.json

  depends_on = [aws_s3_bucket_public_access_block.site]
}
