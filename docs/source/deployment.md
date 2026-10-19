# Deployment

StudySpot has two deployment targets. Both serve the same SvelteKit frontend and the same Django application, and both put the API behind a public `/api` prefix that the edge strips before Django sees the request, so neither deployment needs its own copy of the routes.

| Target | Frontend | API | Database | Driven by |
|---|---|---|---|---|
| Vercel | Vercel service, `adapter-vercel` | Vercel Python service, `main:app` | None by default | Vercel's Git integration |
| AWS | S3 behind CloudFront, prerendered with `adapter-static` | Lambda behind CloudFront `/api/*` | RDS Postgres, private | `just aws-*`, from a laptop |

Vercel is the demo deployment the pull-request workflow is built around: every branch gets a URL and nobody has to run anything. AWS is where the API has a database, because the account funding it can afford a managed Postgres instance and Vercel's free plan cannot. Neither is a staging environment for the other; they are two deployments of one revision.

Vercel's Git integration is the only automatic deployment path. GitHub Actions independently validates the repository, Compose topology, documentation, Nix flake, and Terraform configuration; it does not build or upload a duplicate deployment, and it holds no AWS or Vercel credentials.

## Environments

```text
feature/* -> pull request preview
                  |
                  v
              staging -> staging deployment
                  |
                  v
                main -> production deployment
```

Developers work on short-lived feature branches and open pull requests into `staging`. Nobody pushes feature work directly to `staging`. A reviewed release pull request promotes `staging` into `main`.

Protect both long-lived branches with required checks, resolved conversations, and disabled force pushes and deletion. Repositories with independent reviewers can require approvals; a solo maintainer should leave the approval count at zero because GitHub does not allow authors to approve their own pull requests. A hotfix merged into `main` must immediately be merged back into `staging`.

## Vercel

Every push to `staging` creates a Vercel Preview deployment. The branch domain `dev-studyspot-nyu.vercel.app` tracks the newest successful `staging` deployment. Pushes to `main` update [studyspot-nyu.vercel.app](https://studyspot-nyu.vercel.app).

`vercel.json` defines two services. Requests to `/` use the frontend; `/api/*` uses the Python service, whose own rewrite removes the `/api` prefix so that `/api/health/live` reaches the application's `health/live` route.

Configure Vercel manually:

1. Connect the GitHub repository to the Vercel project.
2. Set `main` as the Production Branch.
3. Assign `dev-studyspot-nyu.vercel.app` to the Preview environment and Git branch `staging`.
4. Assign `studyspot-nyu.vercel.app` to Production.
5. Under **Settings -> Deployment Protection**, choose **None** when both demo domains must be public. **Standard Protection** keeps Preview URLs, including staging, authenticated while leaving production domains public.
6. Set `DJANGO_SECRET_KEY` for both environments. Django refuses to start without one when debug is off.

No Vercel token or project identifiers are required in GitHub Actions. If the repository previously used the duplicate CLI deployment workflow, delete its `VERCEL_TOKEN` secret and `VERCEL_DEPLOY_ENABLED`, `VERCEL_ORG_ID`, and `VERCEL_PROJECT_ID` variables after this change reaches `staging`, then revoke the unused token in Vercel.

Configure GitHub manually:

1. Protect `staging` and `main`.
2. Require `Repository checks`, `Terraform`, `Container smoke test`, `Nix flake`, and `Vercel`.
3. Require resolved conversations and linear history; disable force pushes and deletion.
4. Use zero required approvals for a solo maintainer, or require approvals only when an independent reviewer is available.

The current Vercel project has both aliases assigned, but Deployment Protection redirects anonymous requests to Vercel SSO. Public verification will fail until the protection scope is changed.

```{important}
**The Vercel deployment has no database.** The RDS instance lives in private subnets, and nothing outside its VPC can reach it. Vercel therefore serves the frontend and `GET /api/health/live`, while `GET /api/spots` answers `503 database_unavailable`.

This is a cost decision, not an oversight: reaching the instance from Vercel means setting `database_publicly_accessible = true` and an allowlist in `database_allowed_cidrs`, and Vercel's functions have no stable egress addresses on the plan this project uses, so a workable allowlist is a wide one — a database on the public internet behind one password. Use AWS when the demo needs data.
```

No database secret belongs in GitHub Actions, because nothing in CI deploys. Once Vercel does get a database, give ephemeral previews isolated databases or read-only credentials before adding user-generated writes, and keep staging separate from production.

After making staging public, verify both boundaries and require an exact HTTP 200 rather than accepting redirects:

```shell
test "$(curl --silent --output /dev/null --write-out '%{http_code}' https://dev-studyspot-nyu.vercel.app/)" = 200
curl --fail-with-body --silent --show-error https://dev-studyspot-nyu.vercel.app/api/health/live | grep -Fx '{"status":"ok"}'
```

Promote to production only after the shared staging deployment is public and both web boundaries are verified.

### Manual commands

```shell
just deploy-preview
just deploy-production
```

Nix users can invoke the same commands reproducibly:

```shell
nix run . -- deploy-preview
nix run . -- deploy-production
```

## AWS

The AWS deployment is Terraform in `infra/`: one CloudFront distribution splitting on path, S3 for the prerendered site, a Lambda function running Django through Mangum, and an RDS Postgres instance in private subnets. A second Lambda function runs Django management commands from inside the VPC, because the database has no public endpoint and `manage.py migrate` from a laptop cannot reach it.

A first deployment is seven commands:

```shell
just aws-init
just aws-build
just aws-apply
just aws-migrate
just aws-load
just aws-frontend
just aws-verify
```

Redeploying later is `just aws-build` and `just aws-apply` for the backend, or `just aws-frontend` alone for the frontend.

[`infra/README.md`](https://github.com/2SpaceMasterRace/studyspot/blob/main/infra/README.md) is the source of truth for this target and is not duplicated here. Read it before the first apply: it covers what the stack costs and which lever reduces it, the AWS credentials the Terraform needs, why there is no NAT gateway, how the database password reaches the function, and why Terraform state has to move off a laptop before anyone else touches the stack.

Two things are worth repeating because they are easy to discover too late:

- `just aws-db-stop` stops the database and bills storage only. AWS restarts a stopped instance automatically after seven days, so this is a recurring chore.
- Nothing in the stack is irreplaceable. The infrastructure is `infra/` and the data is `data/spots.json`, so a destroyed stack is one `apply` and one `load` away from working again.

Deployment is manual by design. A GitHub Actions workflow that applied Terraform would need long-lived AWS credentials in the repository, and a course project with one deployment does not need them.

## Data and search state

`data/spots.json` is generated and committed, and the `load_spots` management command copies it into a Postgres database. On AWS, `infra/scripts/build-lambda.sh` bundles the snapshot into the deployment package and `just aws-load` loads it from inside the VPC, so the deployed API serves data as soon as that step has run once. Until it does, `GET /api/spots` returns an empty page rather than an error.

Locally the same step is `just load-data`, after `just start-db` and `just migrate`. The Compose backend runs migrations itself on startup but does not load data, so a fresh volume serves an empty page until you load one.

Runtime search structures are still unbuilt. Meilisearch remains part of the local Compose topology for integration work and is not a deployed dependency of either target.

While every record comes from the normalized public snapshot, any environment's database can be cleared and reloaded. Once StudySpot stores corrections, favorites, accounts, import cursors, or other non-reproducible state, backups and backward-compatible migrations become release requirements.

## Rollback

On Vercel, list deployments and point production back to a known working deployment:

```shell
bunx vercel@59.16.0 list
bunx vercel@59.16.0 rollback DEPLOYMENT_URL
```

On AWS, roll back by checking out the previous revision and running `just aws-build` and `just aws-apply`; the frontend is `just aws-frontend` from the same checkout.

Neither rollback changes database contents. Keep schema changes compatible with the previous application revision, or reload the matching database state separately — which, while the table is a projection of `spots.json`, means loading the snapshot from that revision.
