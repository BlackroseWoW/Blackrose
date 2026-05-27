# mod-worgoblin - SQL conventions

This folder holds every SQL migration the module ships. Most of them live in
`db-world/` and are auto-applied by AzerothCore's module updater on
worldserver start. A few legacy upstream goodies live in `supplementary/`
and are opt-in only.

## Layout

```
data/sql/
├── db-world/         # auto-applied to acore_world by AC's UpdateFetcher
└── supplementary/    # opt-in legacy upstream files (NOT auto-applied)
```

Files dropped into `db-world/` get a SHA1 stored in the `world.updates`
table; AC re-runs them only if the SHA1 changes. Files in `supplementary/`
are never seen by the updater and must be applied by hand if you want
them.

## Migration naming

Use the same pattern Black Rose uses everywhere else:

```
YYYY_MM_DD_NN_<scope>_<short_description>.sql
```

* `YYYY_MM_DD` - calendar date the migration was authored (PT timezone is
  fine).
* `NN`         - 2-digit ordinal that determines apply order on the same
  day. Start at `00` and bump per file.
* `<scope>`    - the module / area, e.g. `worgoblin` for everything in
  this folder.
* `<short_description>` - lowercase, underscore-separated, short.

Concrete examples already in this tree:

```
2026_05_26_00_worgoblin_data.sql
2026_05_26_01_worgoblin_charstartoutfit_dbc.sql
2026_05_27_01_worgoblin_mount_vendor.sql
```

## File-content rules

* Every `INSERT` is preceded by a matching `DELETE` so the migration is
  idempotent. The codestyle linter
  (`apps/codestyle/codestyle-sql.py`) enforces this; CI will reject the
  PR otherwise.
* `acore_world` tables use `InnoDB`.
* 4-space indent, trailing newline, no tabs, no double semicolons.
* DBC mirrors (rows in `*_dbc` tables) match the canonical 3.3.5a column
  set - copy a row off a stock entry instead of inventing column lists.
* Lean on `SET @var := value;` for cross-statement references (entry ids,
  spawn guids, source-types). It keeps the migration self-documenting and
  makes it cheaper to retarget when a single id collides with another
  module.
* Comments at the top of every file: a single `--` header block in the
  Black Rose box-comment style explaining **why** the migration exists and
  what it touches. The migration's first reviewer is usually someone
  six months from now wondering why a value is what it is - help them.

## When to add a new file vs amend an existing one

* If a migration **has not been merged to `main` yet**, amend it in
  place. There's no downside.
* If it **has been merged and applied** to any running realm, write a
  follow-up migration with a fresh date / NN. Editing an applied file
  forces AC's updater to re-run it on every realm; for `INSERT/DELETE`
  files that's fine, but for anything that mutates live data (e.g.
  removing a smart-script row) you really want a separate migration to
  keep the audit trail clean.
