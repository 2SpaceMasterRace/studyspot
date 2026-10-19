# VPC for the API functions and the database.
#
# There is deliberately no NAT gateway. A NAT gateway costs about $32/month
# before data charges, which would be more than every other resource in this
# stack combined, and nothing here needs outbound internet:
#
#   - the API function only talks to Postgres, which lives in this VPC; and
#   - Lambda's own log delivery to CloudWatch runs through the Lambda service
#     rather than through the function's VPC interface, so logging works without
#     a NAT gateway or an interface endpoint.
#
# This is also why the database password reaches the function as an environment
# variable rather than through a Secrets Manager call at runtime: that call would
# require an interface endpoint at roughly $7/month per availability zone. See
# the note in infra/README.md about what that tradeoff costs you in return.

data "aws_availability_zones" "available" {
  state = "available"

  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${local.name_prefix}-vpc"
  }
}

# Public subnets exist so that the database can be given a public address when
# database_publicly_accessible is true. With the default of false nothing is
# placed in them, and they cost nothing to keep.
resource "aws_subnet" "public" {
  count = var.az_count

  vpc_id                  = aws_vpc.main.id
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  map_public_ip_on_launch = false

  tags = {
    Name = "${local.name_prefix}-public-${count.index + 1}"
    Tier = "public"
  }
}

resource "aws_subnet" "private" {
  count = var.az_count

  vpc_id            = aws_vpc.main.id
  availability_zone = data.aws_availability_zones.available.names[count.index]
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)

  tags = {
    Name = "${local.name_prefix}-private-${count.index + 1}"
    Tier = "private"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${local.name_prefix}-igw"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${local.name_prefix}-public"
  }
}

resource "aws_route_table_association" "public" {
  count = var.az_count

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# No routes beyond the VPC-local one. The API function reaches Postgres and
# nothing else, which is the whole of its job.
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${local.name_prefix}-private"
  }
}

resource "aws_route_table_association" "private" {
  count = var.az_count

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# -- Security groups -----------------------------------------------------------

resource "aws_security_group" "lambda" {
  name        = "${local.name_prefix}-lambda"
  description = "StudySpot API functions"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${local.name_prefix}-lambda"
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group" "database" {
  name        = "${local.name_prefix}-database"
  description = "StudySpot Postgres instance"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${local.name_prefix}-database"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Rules are separate resources rather than inline blocks so that the two groups
# can reference each other without a cycle.
resource "aws_vpc_security_group_egress_rule" "lambda_to_database" {
  security_group_id = aws_security_group.lambda.id
  description       = "Postgres"

  referenced_security_group_id = aws_security_group.database.id
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "database_from_lambda" {
  security_group_id = aws_security_group.database.id
  description       = "Postgres from the StudySpot API functions"

  referenced_security_group_id = aws_security_group.lambda.id
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
}

# Only created when the database is public, and only for the CIDRs you name.
resource "aws_vpc_security_group_ingress_rule" "database_from_allowlist" {
  count = var.database_publicly_accessible ? length(var.database_allowed_cidrs) : 0

  security_group_id = aws_security_group.database.id
  description       = "Postgres from an allowlisted network"

  cidr_ipv4   = var.database_allowed_cidrs[count.index]
  from_port   = 5432
  to_port     = 5432
  ip_protocol = "tcp"
}
