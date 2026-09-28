# StudySpot frontend scaffold

This Bun project contains the Svelte 5 search interface for NYC cafés and other third places. Text, radius, and Open now controls send one filtered request to the API and render distance and hours status. The canonical spot dataset is currently empty, so local results require a populated snapshot, `just load-data`, and `just reindex`.

```shell
bun install
bun run dev
bun run check
bun run build
```
