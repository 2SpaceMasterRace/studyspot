# The Postgres serving database.
#
# This replaces Turso. The schema and queries are the same shape they were under
# SQLite, because every consumer already went through one repository interface.

resource "random_password" "database" {
  length = 40

  # Excluded rather than escaped: this password is interpolated into a
  # postgresql:// connection string, and a stray @ or / there produces a DSN that
  # parses as something else entirely.
  special          = true
  override_special = "-_.~"
}

resource "aws_db_subnet_group" "main" {
  name        = "${local.name_prefix}-database"
  description = "StudySpot database subnets"

  subnet_ids = var.database_publicly_accessible ? aws_subnet.public[*].id : aws_subnet.private[*].id

  tags = {
    Name = "${local.name_prefix}-database"
  }
}

resource "aws_db_parameter_group" "main" {
  name        = "${local.name_prefix}-postgres${var.db_engine_version}"
  family      = "postgres${var.db_engine_version}"
  description = "StudySpot Postgres parameters"

  # Reject any connection that is not TLS. This matters most when
  # database_publicly_accessible is true, but costs nothing when it is false, so
  # it is not conditional.
  parameter {
    name  = "rds.force_ssl"
    value = "1"
  }

  # Log statements that take longer than a second. The study-spot queries are
  # indexed lookups; anything slower is worth seeing.
  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_db_instance" "main" {
  identifier = "${local.name_prefix}-database"

  engine         = "postgres"
  engine_version = var.db_engine_version
  instance_class = var.db_instance_class

  # gp3 at the 20 GB floor. Storage autoscaling is capped so that a runaway write
  # cannot quietly grow the bill; the dataset is a few megabytes.
  storage_type          = "gp3"
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_allocated_storage * 2
  storage_encrypted     = true

  db_name  = var.db_name
  username = var.db_username
  password = random_password.database.result
  port     = 5432

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.database.id]
  publicly_accessible    = var.database_publicly_accessible
  parameter_group_name   = aws_db_parameter_group.main.name

  multi_az                   = var.db_multi_az
  backup_retention_period    = var.db_backup_retention_days
  backup_window              = "07:00-08:00"
  maintenance_window         = "Mon:08:30-Mon:09:30"
  auto_minor_version_upgrade = true

  # Performance Insights and enhanced monitoring are both chargeable beyond their
  # free tiers and neither is useful at this size. Postgres logs are enough.
  enabled_cloudwatch_logs_exports = ["postgresql"]

  deletion_protection       = var.db_deletion_protection
  skip_final_snapshot       = var.db_skip_final_snapshot
  final_snapshot_identifier = var.db_skip_final_snapshot ? null : "${local.name_prefix}-database-final"
  copy_tags_to_snapshot     = true

  # apply_immediately is deliberately false: parameter and class changes wait for
  # the maintenance window rather than restarting the database under traffic.
  apply_immediately = false

  tags = {
    Name = "${local.name_prefix}-database"
  }
}

locals {
  # sslmode=require rather than verify-full: the RDS certificate chain would need
  # to be bundled into the Lambda package to verify the hostname, which is worth
  # doing before this database holds anything that is not a public dataset.
  database_url = join("", [
    "postgresql://",
    var.db_username,
    ":",
    urlencode(random_password.database.result),
    "@",
    aws_db_instance.main.address,
    ":",
    tostring(aws_db_instance.main.port),
    "/",
    var.db_name,
    "?sslmode=require",
  ])
}

# Stored so that a human, or the Vercel deployment, can retrieve the connection
# string without reading Terraform state. The functions themselves receive it as
# an environment variable; see the note in network.tf.
resource "aws_secretsmanager_secret" "database" {
  name        = "${local.name_prefix}/database"
  description = "StudySpot Postgres connection details"

  # A demo stack gets torn down and rebuilt often, and Secrets Manager otherwise
  # holds the name for 30 days and refuses to recreate it.
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "database" {
  secret_id = aws_secretsmanager_secret.database.id

  secret_string = jsonencode({
    engine   = "postgres"
    host     = aws_db_instance.main.address
    port     = aws_db_instance.main.port
    dbname   = var.db_name
    username = var.db_username
    password = random_password.database.result
    url      = local.database_url
  })
}
