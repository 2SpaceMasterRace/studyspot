# Input variables for the StudySpot AWS deployment.
#
# Every default is chosen to keep a demo deployment cheap. The comments say what
# each one costs when you raise it, because the difference between this stack at
# ~$15/month and the same stack at ~$80/month is four of these values.

variable "project" {
  description = "Name prefix for every resource."
  type        = string
  default     = "studyspot"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,20}$", var.project))
    error_message = "The project name must be lowercase alphanumeric with hyphens, 2-21 characters."
  }
}

variable "environment" {
  description = "Deployment environment. Used in resource names, so one account can hold several."
  type        = string
  default     = "staging"

  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "The environment must be either staging or production."
  }
}

variable "region" {
  description = "AWS region for everything except the CloudFront certificate."
  type        = string
  default     = "us-east-1"
}

# -- Network -------------------------------------------------------------------

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.20.0.0/16"
}

variable "az_count" {
  description = <<-EOT
    Availability zones to spread subnets across. RDS requires a subnet group with
    at least two, so two is the minimum even for a single-AZ instance.
  EOT
  type        = number
  default     = 2

  validation {
    condition     = var.az_count >= 2 && var.az_count <= 3
    error_message = "Between two and three availability zones are supported."
  }
}

# -- Database ------------------------------------------------------------------

variable "db_instance_class" {
  description = <<-EOT
    RDS instance class. db.t4g.micro is Graviton, the cheapest class that runs
    Postgres, and is covered by the 12-month AWS free tier. db.t4g.small roughly
    doubles the bill.
  EOT
  type        = string
  default     = "db.t4g.micro"
}

variable "db_engine_version" {
  description = "Postgres major version. Minor upgrades are applied automatically."
  type        = string
  default     = "17"
}

variable "db_allocated_storage" {
  description = "Storage in GB. 20 is the gp3 minimum and the free-tier allowance."
  type        = number
  default     = 20
}

variable "db_name" {
  description = "Initial database name."
  type        = string
  default     = "studyspot"
}

variable "db_username" {
  description = "Master username. The password is generated and never committed."
  type        = string
  default     = "studyspot"
}

variable "db_multi_az" {
  description = "Run a standby in a second AZ. Roughly doubles the database cost."
  type        = bool
  default     = false
}

variable "db_backup_retention_days" {
  description = "Automated backup retention. Zero disables backups entirely."
  type        = number
  default     = 7
}

variable "database_publicly_accessible" {
  description = <<-EOT
    Whether the database gets a public endpoint.

    false (default) places RDS in private subnets. Only the Lambda functions in
    this VPC can reach it. This is the safe setting, and it means the Vercel
    deployment has no database to talk to.

    true places RDS in public subnets with a public address, still TLS-only and
    still restricted to database_allowed_cidrs. Set this if you want the existing
    Vercel deployment to keep serving /spots after Turso is retired. The tradeoff
    is a database endpoint reachable from the internet by anyone inside those
    CIDRs, so pair it with a narrow allowlist.
  EOT
  type        = bool
  default     = false
}

variable "database_allowed_cidrs" {
  description = <<-EOT
    CIDR blocks allowed to reach Postgres when database_publicly_accessible is
    true. Vercel does not publish stable egress ranges on every plan, so making
    the Vercel deployment work may mean widening this further than you would
    like; check your plan's documented egress IPs before resorting to 0.0.0.0/0.
  EOT
  type        = list(string)
  default     = []

  validation {
    condition     = alltrue([for cidr in var.database_allowed_cidrs : can(cidrhost(cidr, 0))])
    error_message = "Every entry must be a valid CIDR block."
  }
}

variable "db_deletion_protection" {
  description = "Refuse to destroy the database. Leave this on for production."
  type        = bool
  default     = false
}

variable "db_skip_final_snapshot" {
  description = "Skip the final snapshot on destroy. Convenient for a demo, wrong for production."
  type        = bool
  default     = true
}

# -- Lambda --------------------------------------------------------------------

variable "lambda_package_path" {
  description = <<-EOT
    Path to the deployment zip, relative to this directory. Build it first with
    infra/scripts/build-lambda.sh, which cross-compiles the backend's
    dependencies for the arm64 Lambda runtime.
  EOT
  type        = string
  default     = "../build/studyspot-api.zip"
}

variable "api_memory_mb" {
  description = <<-EOT
    Memory for the API function. Lambda scales CPU with memory, so raising this
    often lowers cost per request by shortening the duration billed.
  EOT
  type        = number
  default     = 512
}

variable "api_timeout_seconds" {
  description = "Request timeout for the API function."
  type        = number
  default     = 15
}

variable "manage_memory_mb" {
  description = <<-EOT
    Memory for the management function. load_spots holds the whole snapshot in
    memory and validates every record before writing.
  EOT
  type        = number
  default     = 1024
}

variable "manage_timeout_seconds" {
  description = "Timeout for management commands. Migrations are the slow case."
  type        = number
  default     = 300
}

variable "lambda_role_arn" {
  description = <<-EOT
    An existing execution role for both functions. Leave empty to have Terraform
    create one, which is what a normal account should do.

    Set it when the account forbids iam:CreateRole and hands you a preset role
    instead, as course lab environments do. The role must allow the Lambda
    service to assume it and must carry AWSLambdaVPCAccessExecutionRole or
    equivalent, or the functions cannot create their network interfaces.
  EOT
  type        = string
  default     = ""
}

# -- Django --------------------------------------------------------------------

variable "django_allowed_hosts" {
  description = <<-EOT
    Value for DJANGO_ALLOWED_HOSTS. The default is permissive because CloudFront
    does not forward the Host header to a Lambda function URL, so the host Django
    sees is the function URL's own rather than anything a viewer controls, and the
    URL already refuses requests that CloudFront has not signed.
  EOT
  type        = string
  default     = "*"
}

variable "django_csrf_trusted_origins" {
  description = <<-EOT
    Origins allowed to submit session-authenticated writes, as full origins such
    as https://d111111abcdef8.cloudfront.net.

    Needed only once the admin or another session-authenticated write exists. It
    is a variable rather than a reference to the distribution because the
    distribution depends on the function URL, and reading its domain from the
    function's environment would be a dependency cycle: apply once, then add the
    printed domain here.
  EOT
  type        = list(string)
  default     = []
}

variable "django_enable_admin" {
  description = <<-EOT
    Mount the Django admin. Off by default: it is reachable from the internet
    through CloudFront, and until the backlog reaches accounts there is nothing
    guarding it but a superuser password nobody has created.
  EOT
  type        = bool
  default     = false
}

variable "log_retention_days" {
  description = "CloudWatch log retention. Logs kept forever are a slow, quiet cost."
  type        = number
  default     = 14
}

# -- Frontend ------------------------------------------------------------------

variable "cloudfront_price_class" {
  description = <<-EOT
    PriceClass_100 covers North America and Europe and is the cheapest. StudySpot
    is a New York City dataset, so the default is deliberate rather than lazy.
  EOT
  type        = string
  default     = "PriceClass_100"

  validation {
    condition     = contains(["PriceClass_100", "PriceClass_200", "PriceClass_All"], var.cloudfront_price_class)
    error_message = "Must be PriceClass_100, PriceClass_200, or PriceClass_All."
  }
}

variable "site_bucket_force_destroy" {
  description = "Allow destroying the site bucket while it still holds objects."
  type        = bool
  default     = true
}
