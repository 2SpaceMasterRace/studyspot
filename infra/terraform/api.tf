# The Django application on Lambda, and management commands beside it.
#
# Both functions ship from one zip built by infra/scripts/build-lambda.sh. They
# differ only in handler, memory, and timeout, which keeps the deployed code and
# the migrations applied to the database provably the same revision.

data "aws_caller_identity" "current" {}

# Django refuses to start without this, and it must not change between
# deployments or every signed cookie and password-reset link is invalidated.
resource "random_password" "django_secret_key" {
  length  = 64
  special = false
}

# -- Execution role ------------------------------------------------------------
#
# Created here unless lambda_role_arn names an existing one. Some locked-down
# accounts, course lab environments in particular, forbid iam:CreateRole and
# hand you a preset role to use instead.

locals {
  create_role     = var.lambda_role_arn == ""
  lambda_role_arn = local.create_role ? aws_iam_role.lambda[0].arn : var.lambda_role_arn
}

resource "aws_iam_role" "lambda" {
  count = local.create_role ? 1 : 0

  name        = "${local.name_prefix}-lambda"
  description = "Execution role for the StudySpot API and management functions"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# Grants the ENI management the VPC attachment needs, and CloudWatch Logs.
resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  count = local.create_role ? 1 : 0

  role       = aws_iam_role.lambda[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# -- Logs ----------------------------------------------------------------------
#
# Declared rather than left to Lambda's implicit creation, so that retention is
# set from the start. A log group Lambda creates itself never expires, and on a
# credit-funded account that is a slow leak.

resource "aws_cloudwatch_log_group" "api" {
  name              = "/aws/lambda/${local.name_prefix}-api"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "manage" {
  name              = "/aws/lambda/${local.name_prefix}-manage"
  retention_in_days = var.log_retention_days
}

# -- Functions -----------------------------------------------------------------

locals {
  lambda_environment = {
    DATABASE_URL = local.database_url

    # TLS to RDS is enforced by the rds.force_ssl parameter in database.tf; this
    # is what makes the client ask for it in the first place.
    DATABASE_SSL_REQUIRE = "true"

    DJANGO_SETTINGS_MODULE = "studyspot.settings"
    DJANGO_SECRET_KEY      = random_password.django_secret_key.result
    DJANGO_DEBUG           = "false"

    # CloudFront does not forward the Host header to a function URL, so the host
    # Django sees is the function URL's own. settings.py explains why validating
    # it would add nothing to the SigV4 signature already required.
    DJANGO_ALLOWED_HOSTS = var.django_allowed_hosts

    # Empty until you enable the admin, at which point this wants the
    # distribution's own domain. It is a variable rather than a reference to the
    # distribution because the distribution depends on the function URL, and
    # reading its domain here would be a dependency cycle.
    DJANGO_CSRF_TRUSTED_ORIGINS = join(",", var.django_csrf_trusted_origins)

    DJANGO_ENABLE_ADMIN = tostring(var.django_enable_admin)

    PYTHONDONTWRITEBYTECODE = "1"
  }

  lambda_vpc_subnets = aws_subnet.private[*].id
}

resource "aws_lambda_function" "api" {
  function_name = "${local.name_prefix}-api"
  description   = "StudySpot Django application"
  role          = local.lambda_role_arn

  filename         = var.lambda_package_path
  source_code_hash = filebase64sha256(var.lambda_package_path)

  runtime = "python3.12"

  # arm64 is cheaper per GB-second than x86_64 and matches the Graviton database
  # instance class. The build script cross-compiles wheels for it accordingly.
  architectures = ["arm64"]
  handler       = "handler.api"

  memory_size = var.api_memory_mb
  timeout     = var.api_timeout_seconds

  environment {
    variables = local.lambda_environment
  }

  vpc_config {
    subnet_ids         = local.lambda_vpc_subnets
    security_group_ids = [aws_security_group.lambda.id]
  }

  depends_on = [
    aws_cloudwatch_log_group.api,
    aws_iam_role_policy_attachment.lambda_vpc,
  ]

  tags = {
    Name = "${local.name_prefix}-api"
  }
}

# Runs migrate, load_spots, collectstatic and showmigrations. It exists because
# the database has no public endpoint by default: nothing on a laptop can reach
# it, so the commands have to run from inside the VPC.
resource "aws_lambda_function" "manage" {
  function_name = "${local.name_prefix}-manage"
  description   = "Runs StudySpot Django management commands inside the VPC"
  role          = local.lambda_role_arn

  filename         = var.lambda_package_path
  source_code_hash = filebase64sha256(var.lambda_package_path)

  runtime       = "python3.12"
  architectures = ["arm64"]
  handler       = "handler.manage"

  memory_size = var.manage_memory_mb
  timeout     = var.manage_timeout_seconds

  environment {
    variables = local.lambda_environment
  }

  vpc_config {
    subnet_ids         = local.lambda_vpc_subnets
    security_group_ids = [aws_security_group.lambda.id]
  }

  depends_on = [
    aws_cloudwatch_log_group.manage,
    aws_iam_role_policy_attachment.lambda_vpc,
  ]

  tags = {
    Name = "${local.name_prefix}-manage"
  }
}

# A function URL rather than API Gateway: CloudFront is already the public edge,
# and an HTTP API would add a second one plus its own per-request charge.
#
# AWS_IAM means the URL is not usable without a signed request. CloudFront signs
# with the origin access control in cdn.tf, so the function is reachable only
# through the distribution.
resource "aws_lambda_function_url" "api" {
  function_name      = aws_lambda_function.api.function_name
  authorization_type = "AWS_IAM"
}

resource "aws_lambda_permission" "api_from_cloudfront" {
  statement_id           = "AllowCloudFrontInvokeFunctionUrl"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.api.function_name
  principal              = "cloudfront.amazonaws.com"
  source_arn             = aws_cloudfront_distribution.main.arn
  function_url_auth_type = "AWS_IAM"
}
