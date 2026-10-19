# Provider requirements for the StudySpot AWS deployment.
#
# Versions are pinned the way the rest of the repository pins its toolchain: a
# `terraform init` a year from now should resolve the same providers this
# configuration was written against.

terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = local.tags
  }
}

# CloudFront requires ACM certificates in us-east-1 regardless of where the rest
# of the stack lives. Nothing uses this provider yet; it is here so that adding a
# custom domain later does not require restructuring the configuration.
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  default_tags {
    tags = local.tags
  }
}

locals {
  name_prefix = "${var.project}-${var.environment}"

  tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
    Repository  = "studyspot"
  }
}
