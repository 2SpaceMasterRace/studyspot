# Frontend Instructions

This Bun project owns the Svelte search experience.

- Use Svelte 5 runes and strict TypeScript.
- Keep components small and colocate component tests under `src/`.
- Treat the shared contract in `contracts/` as the data boundary.
- Use sample data until the API integration ticket begins.
- Use TanStack Query when remote server state is introduced.
- Use Tailwind CSS and shadcn-svelte for reusable interface primitives when a working feature needs them.
- Preserve keyboard access, visible focus, responsive layout, and explicit loading, empty, no-results, and error states.
- Avoid `any`, silent promise failures, duplicated server state, and speculative component layers.
- Add dependencies through Bun and commit `bun.lock`.

Run before handoff:

```shell
bun run lint
bun run check
bun run build
```

The scaffold currently has no frontend tests. Add meaningful tests with the first implemented search behavior, then include `bun run test` in the handoff checks.
