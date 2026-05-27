# mod-worgoblin

AzerothCore module that adds Worgen (race 22 on retail / 12 in WotLK
slot) and Goblin (race 9) as playable races, plus the associated
starting zones, gear, mounts, racial spells, and DBC patches.

Upstream: [benjymansy123/mod-worgoblin](https://github.com/benjymansy123/mod-worgoblin)
(marked "no longer maintained"). This is the Black Rose fork, modernized
to fit the current AzerothCore module layout and the Black Rose client
patch pipeline.

## What it does

**Server side:**

* `src/Worgoblin.cpp` registers a `PlayerScript` that prints a login
  banner and applies the Goblin "Best Deals Anywhere" (spell `69044`)
  20% rep discount, plus a `SpellScript` for the Goblin racial Rocket
  Barrage (`69041`).
* `data/sql/db-world/2026_05_26_00_worgoblin_data.sql` adds race stats,
  totem models, starting zones, starter gear, action bars, racial
  skills, language assignments, achievement criteria, and the Goblin
  trike / Worgen horse mounts.
* `data/sql/db-world/2026_05_26_01_worgoblin_*_dbc.sql` populates the
  server-side DBC mirror tables (`chrraces_dbc`, `creaturedisplayinfo_dbc`,
  `skilllineability_dbc`, ...) so the server agrees with the patched
  client on race / display / skill availability.

Both folders are auto-applied by AzerothCore's module SQL updater
(`UpdateFetcher.cpp` recursively scans `modules/<name>/data/sql/db-*/`),
so the only thing you have to do server-side is rebuild and restart
the worldserver after this module is in `modules/`.

**Client side:**

The module's client-side tree was relocated into the shared clientpatch
pipeline. It now lives at:

* `tools/clientpatch/input/custom/DBFilesClient/*.dbc` - 30 pre-patched
  3.3.5a DBCs that light up the new races in the character creation UI,
  hook up the starter outfit, register racial skills, etc.
* `tools/clientpatch/input/custom/{Character,Creature,ITEM,Interface,Sound,Spells,Textures,World}/`
  - 6k+ model / texture / skin / lua / ogg assets that the racial
  models reference.

The Black Rose client patch builder
(`tools/clientpatch/build_patch.py`) treats that tree as the
`input/custom/` layer underneath the Black Rose JSON overlays and packs
everything into the same `patch-Z.MPQ`. See
[tools/clientpatch/README.md](../../tools/clientpatch/README.md#input-layers)
for the layering details.

## Optional / opt-in content

`data/sql/supplementary/` ships four legacy SQL files from the upstream
module: `dk-quests.sql`, `optional-class-quests.sql`,
`optional-class-trainers.sql`, `optional-mount-vendor.sql`. They are
**not** under `db-world/` so AzerothCore's auto-updater does **not**
apply them. They also still use the old (pre-`creature_template_model`)
`creature_template` schema with `modelid1..4`, `trainer_type`,
`mechanic_immune_mask`, etc. - they will fail on modern AC as-is.

Bring them in only if you want the upstream's optional flavor content,
and only after porting them to the modern schema (move models into
`creature_template_model`, trainers into `npc_trainer`, etc.).

## Installation

The module is already wired into the Black Rose tree:

* Server-side source / SQL in `modules/mod-worgoblin/` (this folder).
* `.gitignore` exception so the whole tree is tracked.
* Client-side assets live under `tools/clientpatch/input/custom/` and
  are picked up automatically by `build_patch.py` - no code change
  needed to add new module assets, just drop them into that tree.

To enable / disable the server-side scripts, use AzerothCore's standard
CMake module switches. Static (default) builds pick the module up
automatically; pass `-DDISABLED_AC_MODULES="mod-worgoblin"` to skip it.

## Building the client patch

From the repo root:

```bash
cd tools/clientpatch
# 1) Extract vanilla DBCs into input/stock/DBFilesClient/ (one-time, see
#    that folder's README for priority order across patch-3.MPQ etc.).
python3 build_patch.py merge
# 2) Pack staging/ into output/patch-Z.MPQ (MPQ format v1) using Ladik's
#    MPQ Editor or smpq.
```

The merge log will show worgoblin's DBCs coming through as the base for
`Spell.dbc`, `SkillLineAbility.dbc`, `Item.dbc`, and `ItemDisplayInfo.dbc`,
and as straight pass-through for the other 26 DBCs the module ships.

## What changed vs upstream

* Folder renamed `mod-worgoblin-master/` -> `mod-worgoblin/` to match
  AzerothCore's module discovery (the loader function the build
  generates is derived from the folder name: `Addmod_worgoblinScripts`).
* Loader split out of a header: `worgoblin_loader.cpp` defines
  `Addmod_worgoblinScripts()` (was previously inline in a header that
  only worked because exactly one `.cpp` included it - fragile).
* `data/sql/db-world/worgoblin.sql` -> `data/sql/db-world/2026_05_26_00_worgoblin_data.sql`
  and the 17 `data/sql/db-world/workflow/*_dbc.sql` files are flattened
  up one level with a `2026_05_26_01_worgoblin_` prefix. This gives the
  DBC mirror SQLs unique filenames (AC's updater fails on duplicates)
  and the standard `YYYY_MM_DD_NN_` ordering.
* Upstream's `data/patch/` tree (the 6.5k client-side DBCs + assets)
  was moved out of the module into `tools/clientpatch/input/custom/`
  so the Black Rose clientpatch pipeline owns all client data
  uniformly. The module itself is now pure C++ + SQL.
* Client patch is no longer applied by manually dropping DBCs into
  AzerothCore's `Data/` directory (the upstream README's step 2). The
  server picks them up via the SQL mirror tables; the client picks
  them up via the Black Rose patch builder.

## Credits

* mthsena, Helias, yuan2105, Tanados, Trimitor#3873, and the upstream
  benjymansy123/mod-worgoblin contributors. The original upstream
  README has the full credits list - see `LICENSE`.

## License

GPLv3, same as upstream. See `LICENSE`.
