# Contributing

## Commit convention (Conventional Commits)

Commits drive versioning and the changelog automatically, so the message format matters:

```
<type>(<optional scope>): <summary>

<optional body>

<optional footer, e.g. BREAKING CHANGE: ...>
```

**Types → version bump** (on merge to `main`):

| Type | Bump | Use for |
|------|------|---------|
| `feat` | minor (`1.2.0`) | new user-facing capability |
| `fix` | patch (`1.1.1`) | bug fix |
| `perf`, `refactor` | patch | performance / internal rework |
| `docs`, `style`, `test`, `build`, `ci`, `chore` | none | no release |
| any type with `!` or a `BREAKING CHANGE:` footer | major (`2.0.0`) | incompatible change |

Examples: `feat(rugby): add reconcile endpoint`, `fix(naming): collapse doubled dot`, `feat(api)!: drop v1 routes`.

## Releases (automated)

There is **no manual version bump or tag**. On every push to `main`, CI (`.github/workflows/ci.yml`):

1. runs backend + frontend + security + docker checks;
2. runs [python-semantic-release](https://python-semantic-release.readthedocs.io) — reads the commits since the last tag, and **if** any are releasing (`feat`/`fix`/`perf`/`refactor`), bumps `app/main.py:__version__` + `pyproject.toml`, regenerates `CHANGELOG.md`, commits, tags `vX.Y.Z`, and creates the GitHub release;
3. builds and pushes the multi-arch image: `:main` on every push, plus `:X.Y.Z`, `:X.Y`, and `:latest` when a release was cut.

Config lives in `pyproject.toml` under `[tool.semantic_release]`.
