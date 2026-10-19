# AWS infrastructure

StudySpot's AWS deployment, defined in Terraform. The Vercel deployment is
unchanged and still described in [`docs/source/deployment.md`](../docs/source/deployment.md);
this is a second, independent target.

```text
                        CloudFront
                       /          \
          /api/*  -->  Lambda  -->  RDS Postgres   (private subnets)
              /*  -->  S3                           (prerendered SvelteKit)
```

One distribution owns the public hostname and splits on path, reproducing the
same boundary `vercel.json` defines. `/api/*` is signed through to a Lambda
function URL with the `/api` prefix stripped at the edge, so Django sees
`/spots` exactly as it does locally.

## What it costs

Everything bills against your AWS credits. At demo traffic Lambda, CloudFront
and S3 are rounding errors; the database is effectively the whole bill.

| Resource | Monthly |
|---|---|
| RDS `db.t4g.micro`, 20 GB gp3, single-AZ | ~$13 |
| Secrets Manager, one secret | $0.40 |
| S3, CloudFront, Lambda, CloudWatch at demo traffic | under $1 |
| **Total** | **~$15** |

The database is the lever. `just aws-db-stop` stops it and bills storage only,
about $2.50/month; AWS restarts a stopped instance automatically after seven
days, so stopping it again is a recurring chore rather than a one-off.

Two things that are easy to get wrong on a credit-funded account:

- **Do not let the account join an AWS Organization or set up a Control Tower
  landing zone.** Either one force-upgrades the account to a paid plan and
  expires the remaining credits immediately.
- **When a free plan expires, AWS closes the account** and the resources go with
  it. Data is retained for 90 days and upgrading restores access. This is the
  reason the stack is defined here rather than clicked together in the console:
  the infrastructure is this directory and the data is `data/spots.json`, so
  rebuilding is one `apply` and one `load`.

## Prerequisites

The AWS CLI and Terraform are pinned in `flake.nix` alongside the rest of the
toolchain, so a Nix checkout already has them:

```bash
direnv reload          # or: nix develop
aws --version && terraform version
```

Without Nix, note that Terraform left homebrew-core when its license changed:

```bash
brew install awscli && brew tap hashicorp/tap && brew install hashicorp/tap/terraform
```

Then give the CLI credentials. `aws configure sso` is correct only if the
account has IAM Identity Center set up; a personal account normally does not,
in which case create an IAM user, attach `AdministratorAccess`, generate an
access key for the CLI, and run:

```bash
aws configure
aws sts get-caller-identity
```

Create that key on an IAM user rather than on the account root. Root keys cannot
be scoped, revoking one is awkward, and this one lives in `~/.aws/credentials`
in cleartext with full billing access to the account holding your credits.

The Terraform needs EC2 (VPC, subnets, security groups), RDS, Lambda, S3,
CloudFront, Secrets Manager, CloudWatch Logs, and IAM — specifically
`iam:CreateRole`, `iam:AttachRolePolicy` and `iam:PassRole`, because the API
function needs an execution role. If your account forbids creating roles, set
`lambda_role_arn` to a role you have been given and Terraform will skip creating
one.

## First deployment

```bash
just aws-init
just aws-build
just aws-apply
just aws-migrate
just aws-load
just aws-frontend
just aws-verify
```

What each step is for:

1. **`aws-init`** downloads the providers.
2. **`aws-build`** cross-compiles the Lambda package for arm64 Linux. Terraform
   reads its hash, so this has to run before any apply that changes backend
   code.
3. **`aws-apply`** creates the infrastructure. First run takes roughly ten
   minutes, almost all of it RDS.
4. **`aws-migrate`** applies Django migrations. It runs as a Lambda invocation
   because the database has no public endpoint: nothing on your laptop can
   reach it.
5. **`aws-load`** loads the `data/spots.json` snapshot bundled into the package.
   Until this runs, `/api/spots` returns an empty page rather than an error.
6. **`aws-frontend`** builds the prerendered SvelteKit site with
   `DEPLOY_TARGET=aws`, syncs it to S3, and invalidates the cache.
7. **`aws-verify`** checks that both boundaries answer.

Redeploying later is `aws-build` plus `aws-apply` for the backend, or
`aws-frontend` alone for the frontend.

## Decisions worth knowing about

**No NAT gateway.** A NAT gateway costs about $32/month, more than everything
else here combined. The API function needs no outbound internet: it talks to
Postgres inside the VPC, and Lambda's log delivery to CloudWatch runs through
the Lambda service rather than through the function's network interface.

**The database password reaches the function as an environment variable**, not
through a Secrets Manager call at runtime. Reading it at runtime from a private
subnet would need an interface endpoint at roughly $7/month per availability
zone. The cost of that choice is real: the value is visible to anyone with
`lambda:GetFunction` and it sits in Terraform state in cleartext, which is why
`bootstrap-state.sh` creates an encrypted, versioned, TLS-only state bucket
before anyone shares this stack.

**The database is private by default.** `database_publicly_accessible = false`
means only this VPC can reach it, and the Vercel deployment therefore has no
database. If you want Vercel serving `/spots` too, set that variable and
`database_allowed_cidrs` — see the notes in `terraform.tfvars.example`, because
a wide allowlist is a database exposed to the internet behind one password.

**Caching is off for `/api/*`.** Serving a stale page of spots from the edge
would be a silent correctness problem. Turn it on when the API sends its own
cache headers.

## Files

| File | What it holds |
|---|---|
| `terraform/network.tf` | VPC, subnets, route tables, security groups |
| `terraform/database.tf` | RDS instance, parameter group, generated password |
| `terraform/api.tf` | Lambda functions, execution role, function URL |
| `terraform/web.tf` | Static site bucket |
| `terraform/cdn.tf` | CloudFront distribution and the two edge rewrites |
| `terraform/functions/` | CloudFront Functions, as JavaScript |
| `scripts/build-lambda.sh` | Cross-compiles the deployment package |
| `scripts/bootstrap-state.sh` | Creates the remote state bucket, run once |

## State

State is local until you run `scripts/bootstrap-state.sh`. Local state is fine
for one person on one machine and wrong for anything shared: it holds the
generated database password in cleartext, and two people applying from two
checkouts will overwrite each other's record of what exists. Before a teammate
or CI touches this stack, run that script and follow the instructions it prints.

## Checking the configuration

```bash
just infra-check
```

`terraform validate` evaluates the deployment package's hash, so build the
package first or create a placeholder at `infra/build/studyspot-api.zip`. CI
does the latter, which is why the Terraform job needs no AWS credentials.
