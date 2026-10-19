# What the deployment scripts and a human need after an apply.

output "site_url" {
  description = "The public StudySpot URL."
  value       = "https://${aws_cloudfront_distribution.main.domain_name}"
}

output "api_health_url" {
  description = "Liveness endpoint, for verifying a deployment the way the docs do."
  value       = "https://${aws_cloudfront_distribution.main.domain_name}/api/health/live"
}

output "site_bucket" {
  description = "Bucket the frontend build is synced into."
  value       = aws_s3_bucket.site.bucket
}

output "cloudfront_distribution_id" {
  description = "Distribution to invalidate after syncing a new frontend build."
  value       = aws_cloudfront_distribution.main.id
}

output "api_function_name" {
  description = "Lambda function serving the API."
  value       = aws_lambda_function.api.function_name
}

output "manage_function_name" {
  description = "Lambda function that runs migrate, load_spots and collectstatic."
  value       = aws_lambda_function.manage.function_name
}

output "database_endpoint" {
  description = "Postgres host:port. Only reachable from outside the VPC when the database is public."
  value       = aws_db_instance.main.endpoint
}

output "database_publicly_accessible" {
  description = "Whether anything outside this VPC, such as the Vercel deployment, can reach the database."
  value       = var.database_publicly_accessible
}

output "database_secret_name" {
  description = "Secrets Manager entry holding the connection string."
  value       = aws_secretsmanager_secret.database.name
}

output "database_url" {
  description = "Postgres connection string. Marked sensitive so it stays out of CI logs."
  value       = local.database_url
  sensitive   = true
}

output "database_identifier" {
  description = "RDS instance identifier, for stopping and starting it to preserve credits."
  value       = aws_db_instance.main.identifier
}
