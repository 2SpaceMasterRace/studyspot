# Agent readiness

Audit readiness on a 0–2 scale in five categories.

| Category | 0 | 1 | 2 |
|---|---|---|---|
| Discoverability | No instructions | Partial instructions | Root and scoped instructions agree |
| Setup | Undocumented | Multiple manual paths | One verified setup command |
| Ownership | Unclear | Informal ownership | Paths and shared review rules documented |
| Checks | Missing | Some local checks | Local hooks and CI run the same complete checks |
| Safety | No guardrails | Written rules | Automated secret and destructive-action guards |

Record evidence beside each score. Do not award points for planned files or commands.

## Current scaffold

- Discoverability: 2
- Setup: 1
- Ownership: 2
- Checks: 1
- Safety: 1

**Total: 7/10**

The handoff target is 9/10. A fresh-clone rehearsal is required before claiming 10/10.
