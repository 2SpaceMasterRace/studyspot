# Contributing to StudySpot

## Before you start

1. Confirm the ticket's public contract and definition of done.
2. Run `just setup` from the repository root.
3. Create a short-lived branch from `staging` for one ticket.

If you use Nix, run `nix develop` before `just setup`. The shell provides the repository toolchain but still expects Docker to be running on the host.

## While you work

- Stay within your ownership boundary when possible.
- Ask affected owners to review shared contract or root configuration changes.
- Add dependencies only when the ticket uses them.
- Keep commits focused, understandable, and imperative.
- Preserve a working `main` branch.

## Before opening a pull request

Run:

```shell
just check
```

Run the relevant tests once the ticket has added them. Describe the behavior changed, the checks run, and any measured performance in the pull request.

Never commit `.env` files or credentials. Copy `.env.example` to `.env` only when you need to override the safe local Compose defaults.

Open feature pull requests into `staging`. After the shared staging deployment is verified, open a release pull request from `staging` into `main`. Do not push feature work directly to either long-lived branch. If an emergency fix lands on `main`, merge it back into `staging` immediately.
