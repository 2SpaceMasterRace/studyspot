# The CloudFront distribution: one public hostname in front of both services.
#
# This reproduces the path split vercel.json already defines, so the deployed
# contract does not change between the two hosting providers:
#
#   /api/*  -> the FastAPI function, with the /api prefix stripped
#   /*      -> the static SvelteKit build in S3

data "aws_cloudfront_cache_policy" "caching_optimized" {
  name = "Managed-CachingOptimized"
}

data "aws_cloudfront_cache_policy" "caching_disabled" {
  name = "Managed-CachingDisabled"
}

# Forwards everything the API needs except Host. Host must not be forwarded to a
# Lambda function URL: the URL's own hostname is part of what the SigV4 signature
# covers, so overwriting it makes CloudFront's signed request invalid.
data "aws_cloudfront_origin_request_policy" "all_viewer_except_host" {
  name = "Managed-AllViewerExceptHostHeader"
}

data "aws_cloudfront_response_headers_policy" "security_headers" {
  name = "Managed-SecurityHeadersPolicy"
}

resource "aws_cloudfront_origin_access_control" "site" {
  name                              = "${local.name_prefix}-site"
  description                       = "StudySpot static site bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_origin_access_control" "api" {
  name                              = "${local.name_prefix}-api"
  description                       = "StudySpot API function URL"
  origin_access_control_origin_type = "lambda"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# -- Edge rewrites -------------------------------------------------------------

resource "aws_cloudfront_function" "api_rewrite" {
  name    = "${local.name_prefix}-api-rewrite"
  runtime = "cloudfront-js-2.0"
  comment = "Strips the public /api prefix before the request reaches FastAPI"
  code    = file("${path.module}/functions/api-rewrite.js")
  publish = true
}

resource "aws_cloudfront_function" "site_rewrite" {
  name    = "${local.name_prefix}-site-rewrite"
  runtime = "cloudfront-js-2.0"
  comment = "Serves the SvelteKit shell for routes that are not files in S3"
  code    = file("${path.module}/functions/site-rewrite.js")
  publish = true
}

# -- Distribution --------------------------------------------------------------

resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "StudySpot ${var.environment}"
  default_root_object = "index.html"
  price_class         = var.cloudfront_price_class

  origin {
    origin_id                = "site"
    domain_name              = aws_s3_bucket.site.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.site.id
  }

  origin {
    origin_id                = "api"
    domain_name              = trimsuffix(trimprefix(aws_lambda_function_url.api.function_url, "https://"), "/")
    origin_access_control_id = aws_cloudfront_origin_access_control.api.id

    custom_origin_config {
      origin_protocol_policy = "https-only"
      http_port              = 80
      https_port             = 443
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    target_origin_id       = "site"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD"]

    cache_policy_id            = data.aws_cloudfront_cache_policy.caching_optimized.id
    response_headers_policy_id = data.aws_cloudfront_response_headers_policy.security_headers.id

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.site_rewrite.arn
    }
  }

  ordered_cache_behavior {
    path_pattern           = "/api/*"
    target_origin_id       = "api"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    # The current API is read-only, but a cached POST is the kind of thing that
    # is discovered late, so the write methods are allowed and uncached now.
    allowed_methods = ["GET", "HEAD", "OPTIONS", "PUT", "PATCH", "POST", "DELETE"]
    cached_methods  = ["GET", "HEAD"]

    # Caching stays off until the API sends its own cache headers. Serving a
    # stale page of spots from the edge would be a silent correctness problem.
    cache_policy_id            = data.aws_cloudfront_cache_policy.caching_disabled.id
    origin_request_policy_id   = data.aws_cloudfront_origin_request_policy.all_viewer_except_host.id
    response_headers_policy_id = data.aws_cloudfront_response_headers_policy.security_headers.id

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.api_rewrite.arn
    }
  }

  # No custom_error_response blocks. They apply to every behavior in the
  # distribution, so mapping 404 to the SvelteKit shell would also rewrite the
  # API's own 404 and 503 bodies into HTML. site-rewrite.js handles the frontend
  # case at the edge instead, leaving API errors untouched.

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Name = "${local.name_prefix}-cdn"
  }
}
