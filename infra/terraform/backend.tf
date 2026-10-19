# Terraform state location.
#
# State is local by default so that `terraform init` works immediately after a
# clone. Local state is fine for one person on one machine and wrong for anything
# shared: it holds the generated database password in cleartext, and two people
# applying from two checkouts will overwrite each other's record of reality.
#
# Before a second person or CI touches this stack, run
#
#     infra/scripts/bootstrap-state.sh
#
# which creates a versioned, encrypted state bucket with lockfile-based locking,
# then uncomment the block below and run `terraform init -migrate-state`.
#
# terraform {
#   backend "s3" {
#     bucket       = "studyspot-terraform-state-<account-id>"
#     key          = "staging/terraform.tfstate"
#     region       = "us-east-1"
#     encrypt      = true
#     use_lockfile = true
#   }
# }
