# StudySpot documentation

StudySpot is an instant search demo for cafés and other New York City third places derived from NYC Open Data. This documentation explains how to develop, operate, and extend the system without obscuring which product capabilities are still planned.

```{important}
The service topology, health endpoint, shared study-spot model and migrations, dataset loader, study-spot listing and detail routes, and both deployment targets are implemented. The NYC Open Data importer is still a placeholder, and search behavior and readiness reporting remain planned work.
```

```{toctree}
:maxdepth: 2
:caption: Start here

getting-started
local-development
docker
nix
```

```{toctree}
:maxdepth: 2
:caption: System design

architecture
api
data-and-search
database
```

```{toctree}
:maxdepth: 2
:caption: Delivery

testing
deployment
```

```{toctree}
:maxdepth: 1
:caption: Project

contributing
```
