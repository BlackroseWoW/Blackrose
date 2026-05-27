# Black Rose client patch builder

Generates the binary DBC files for a 3.3.5a (build 12340) client patch that
matches the Black Rose server module. Covers the **bag**, **gem**,
**trinket**, **currency**, **custom item icons**, and **Rurik's Death
Mobile** mount in one build pipeline.

It also ships the **mod-worgoblin** client tree (custom Worgen/Goblin
race assets and pre-patched DBCs) as the `input/custom/` layer underneath
the Black Rose JSON overlays, so the merged `patch-Z.MPQ` carries both
customizations at once. See [Input layers](#input-layers) below.

The mount intentionally reuses the stock 3.3.5a Mechano-Hog client model -
no custom M2/.skin/.blp assets are shipped, so the patch is small and the
client cannot reject a malformed model. The server-side spell
`spell_dbc.EffectMiscValue_1 = 29929` points the mount aura at the
stock "Mechano-hog" creature (entry `29929`); AC's
`AuraEffect::HandleAuraMounted` looks the display up via
`creature_template_model` at mount time.

## What this produces

A `staging/` tree ready to pack into `output/patch-Z.MPQ`:

* **Nine merged DBC files** under `staging/DBFilesClient/` (item, spell,
  and enchant data the client needs for tooltips and right-click behavior;
  these absorb the JSON overlays).
* **26 passthrough DBC files** under `staging/DBFilesClient/`
  (mod-worgoblin's other pre-patched DBCs: `ChrRaces`, `CharSections`,
  `CreatureDisplayInfo`, etc.).
* **mod-worgoblin's full asset tree** mirrored under `staging/Character/`,
  `staging/Creature/`, `staging/ITEM/`, `staging/Interface/`,
  `staging/Sound/`, `staging/Spells/`, `staging/Textures/`,
  `staging/World/` (M2 / skin / blp / anim / ogg).
* **Black Rose item icons** under `staging/Interface/Icons/`
  (29 `INV_BR_*.blp` files referenced by `ItemDisplayInfo.dbc`).

The DBCs:

| DBC                            | Black Rose rows added                                                                            |
|--------------------------------|--------------------------------------------------------------------------------------------------|
| `Spell.dbc`                    | Black Rose aura/use spells, gem and bag upgrade spells, Rurik's Death Mobile, and Rosy's Magic Stick use spell |
| `SpellDuration.dbc`            | `900900` 20 second duration                                                                      |
| `SpellItemEnchantment.dbc`     | 98 rows: red `900300..900386` and yellow `900400..900446` socket enchant tooltips                |
| `GemProperties.dbc`            | Same 98 IDs, red Type=2 / yellow Type=4                                                          |
| `ItemExtendedCost.dbc`         | `900700..900706` Black Miasma costs, `900710..900716` Black Petals costs, and `900720..900726` Black Thorns costs |
| `SkillLineAbility.dbc`         | `900903` registers Rurik's Death Mobile under the Riding skill line so it shows in the mount UI  |
| `QuestSort.dbc`                | `9009` "The Black Rose" header, referenced by `quest_template.QuestSortID = -9009`               |
| `Item.dbc`                     | One row per `item_template` entry in `[900100,901399]` (bags, trinket, mount item, gem upgrades, currencies, gems, and Rosy's sticks). Without these the client misclassifies custom items and breaks right-click. |
| `ItemDisplayInfo.dbc`          | Custom display IDs for The Black Rose, currencies, Ribbons, Mists, Jewels, and Rosy's sticks, pointing at BLP basenames in `input/custom/Interface/Icons/` |

These mirror the server `*_dbc` rows and the live `item_template` table
in `modules/mod-blackrose/data/sql/db-world/`, so client tooltips,
socket lines, the mount UI entry, and right-click behavior match what
the server enforces.

## How Item Icons Resolve

Custom item icons require both DBC mappings and the BLP assets. The client
does not have a separate icon manifest DBC; for 3.3.5a the item icon chain is:

```
Item.dbc item ID -> DisplayInfoID
ItemDisplayInfo.dbc DisplayInfoID -> InventoryIcon_1 basename
Interface\Icons\<InventoryIcon_1>.blp -> rendered icon
```

The server-side mirror is `item_template.displayid` plus
`itemdisplayinfo_dbc`, but the game client still needs its own patched
`DBFilesClient\Item.dbc` and `DBFilesClient\ItemDisplayInfo.dbc` inside the
MPQ. Shipping only `Interface\Icons\*.blp` is not enough; the client will have
the image files but no mapping from custom item/display IDs to those basenames.

Inside the packed MPQ the paths must be rooted exactly like this:

```
DBFilesClient\Item.dbc
DBFilesClient\ItemDisplayInfo.dbc
Interface\Icons\INV_BR_Misc_BlackMiasma.blp
Interface\Icons\INV_BR_Misc_StarkRibbon.blp
Interface\Icons\INV_BR_Misc_RosysMagicStick.blp
```

Do not pack the `staging/` folder itself as a top-level folder. If the archive
contains `staging\DBFilesClient\Item.dbc` or `staging\Interface\Icons\...`, the
client will not load those files.

If you ever want to swap the stock Mechano-Hog model for a custom mount,
re-add `creaturedisplayinfo` and `creaturemodeldata` to `_generate.py` and
to `DEFINITION_TO_SCHEMA` in `build_patch.py`. The schemas for both DBCs
are still defined in `dbc.py` so it's purely an additive change. You'll
also want to drop the M2 bundle under `input/custom/Creature/<MountName>/`
so it gets staged alongside the patched DBCs - see the older git history
of this folder for an example using `tools/models/geargrinder/`.

## Layout

```
tools/clientpatch/
  README.md                 - this file
  build_patch.py            - CLI: stock + custom + JSON overlays -> staging/
  dbc.py                    - WDBC binary read/write + 3.3.5a schemas
  dump_items.py             - dumps item_template rows to definitions/item.json
  definitions/              - JSON row data for each DBC (committed)
    _generate.py            - regenerates the JSONs from compact tables
    spell.json
    spellduration.json
    spellitemenchantment.json
    gemproperties.json
    itemextendedcost.json
    skilllineability.json
    questsort.json
    item.json               - regenerated by dump_items.py from live MySQL
    itemdisplayinfo.json    - custom item icon display rows
  input/
    stock/                  - vanilla Blizzard DBCs (gitignored, you extract)
      DBFilesClient/        - Spell.dbc, GemProperties.dbc, Item.dbc, ... (vanilla)
    custom/                 - committed custom client tree (the project's deliverable)
      DBFilesClient/        - 30 pre-patched DBCs (mod-worgoblin: ChrRaces, ...)
      Character/            - mod-worgoblin race model trees (M2 / skin / blp)
      Creature/             - mod-worgoblin mount and NPC models
      ITEM/                 - mod-worgoblin cataclysm item-model backports
      Interface/            - mod-worgoblin UI screens + Black Rose item icons
        Icons/              - 12 worgoblin `ability_racial_*.blp`
                              + 29 Black Rose `INV_BR_*.blp`
      Sound/                - mod-worgoblin racial emote and vocal UI sounds
      Spells/               - mod-worgoblin racial spell visuals
      Textures/, World/     - mod-worgoblin support assets
  staging/                  - build output (gitignored)
    DBFilesClient/          - patched DBCs (9 merged + 26 passthrough)
    Character/, Interface/, ...  - mirrored from input/custom/
  output/                   - final MPQ (gitignored)
    patch-Z.MPQ
```

Only `input/stock/`, `staging/`, and `output/` are gitignored:

* `input/stock/` holds copyrighted Blizzard DBCs that ship with the
  client; we never commit those.
* `staging/` and `output/` are pure build artefacts.

Everything else - definitions, custom DBCs, custom assets - is
committed source.

## Input layers

`build_patch.py merge` combines three layers into `staging/`:

1. **Stock layer** (`input/stock/DBFilesClient/*.dbc`) - vanilla 3.3.5a
   DBCs the user extracted from their reference client. Provides bases
   for the five DBCs nobody pre-patches (`SpellDuration`,
   `SpellItemEnchantment`, `GemProperties`, `ItemExtendedCost`,
   `QuestSort`).
2. **Custom layer** (`input/custom/`, committed). For every DBC under
   `input/custom/DBFilesClient/`, that file replaces the stock DBC as
   the effective base for the next layer. mod-worgoblin pre-patches
   `Spell.dbc`, `SkillLineAbility.dbc`, `Item.dbc`,
   `ItemDisplayInfo.dbc` (the four overlay-targeted DBCs the JSON
   layer also writes to), plus 26 other DBCs that are only relevant to
   custom races. All non-DBC files (M2 / skin / blp / anim / ogg /
   lua / xml) are copied verbatim into `staging/`.
3. **Overlay layer** (`definitions/*.json`). JSON rows are upserted
   into the effective base DBC (stock or custom-patched) for the nine
   DBCs Black Rose touches.

So for `Item.dbc` the effective stack is:

```
stock Item.dbc  ->  custom Item.dbc (mod-worgoblin)  ->  + Black Rose item rows
```

and for `ChrRaces.dbc`, which only mod-worgoblin patches and no JSON
overlay touches:

```
stock ChrRaces.dbc  ->  custom ChrRaces.dbc (passthrough straight to staging/)
```

The merge log annotates which layer supplied each DBC's base, e.g.

```
  Item.dbc            base=46149 ... <- tools/clientpatch/input/custom/DBFilesClient/Item.dbc
  SpellDuration.dbc   base=  130 ... <- tools/clientpatch/input/stock/DBFilesClient/SpellDuration.dbc
```

To add another module's client patch, drop its files into
`input/custom/` (preserving in-MPQ paths). No code change required;
the pipeline picks them up automatically.

## Server-side counterpart

mod-worgoblin's patched DBCs also need their content mirrored in the
world DB so the server agrees with the client (race/class restrictions,
display IDs, etc.). Those mirrors live in
`modules/mod-worgoblin/data/sql/db-world/2026_05_26_01_worgoblin_*_dbc.sql`
and are applied automatically by AzerothCore's module SQL updater on
worldserver startup. No manual `DBFilesClient/` copy into your
AzerothCore install is required - the **server reads from the SQL
mirror tables**, and the **client reads from the MPQ-packed DBCs**.

## Quick start

### 1. Verify the toolchain (no client needed)

```bash
cd tools/clientpatch
python3 build_patch.py customonly
```

That writes DBCs containing **only** the Black Rose rows into
`staging/DBFilesClient/`. They are not a usable client patch on their own
because they would replace the client's full Spell.dbc with three rows. They
are useful for verifying the writer and inspecting individual rows in
WDBXEditor / MyDBCEditor.

### 2. Extract stock DBCs from your reference client

You need the current authoritative DBCs. For most 3.3.5a clients the DBCs
live in the locale archives under `WoW/Data/enUS/`, not just the root
`WoW/Data/patch-3.MPQ`.

Open the archives below in priority order and extract the newest available
copy of each required DBC into `input/stock/DBFilesClient/`:

```
WoW/Data/enUS/patch-enUS-3.MPQ
WoW/Data/enUS/patch-enUS-2.MPQ
WoW/Data/enUS/patch-enUS.MPQ
WoW/Data/patch-3.MPQ
WoW/Data/patch-2.MPQ
WoW/Data/patch.MPQ
WoW/Data/common-2.MPQ
WoW/Data/common.MPQ
WoW/Data/enUS/locale-enUS.MPQ
```

Required files:

```
input/stock/DBFilesClient/Spell.dbc
input/stock/DBFilesClient/SpellDuration.dbc
input/stock/DBFilesClient/SpellItemEnchantment.dbc
input/stock/DBFilesClient/GemProperties.dbc
input/stock/DBFilesClient/ItemExtendedCost.dbc
input/stock/DBFilesClient/SkillLineAbility.dbc
input/stock/DBFilesClient/QuestSort.dbc
input/stock/DBFilesClient/Item.dbc
input/stock/DBFilesClient/ItemDisplayInfo.dbc
```

Later archives in the load chain override earlier ones. If you extract by
hand, keep the newest/highest-priority copy of each DBC.

### 3. Build the merged patch

```bash
python3 build_patch.py merge
```

The tool first mirrors `input/custom/` into `staging/` (mod-worgoblin's
asset tree + the Black Rose item icons + the 26 passthrough DBCs), then
for each of the nine overlay-targeted DBCs reads the effective base
(`input/custom/DBFilesClient/<file>` if present, else
`input/stock/DBFilesClient/<file>`), upserts the Black Rose JSON rows by
`ID`, sorts by ID, and writes the merged result to
`staging/DBFilesClient/`. Finally it validates that every custom
`ItemDisplayInfo.dbc` icon basename has a matching staged BLP file.

Output looks like:

```
  copied 6509 custom asset(s) into staging/ (26 DBCs straight-copied; overlay DBCs are merged below)
  Spell.dbc                  base= 49855 custom=  7 added=  5 merged=  2 total= 49860   <- input/custom/DBFilesClient/Spell.dbc
  SpellDuration.dbc          base=   130 custom=  1 added=  1 merged=  0 total=   131   <- input/stock/DBFilesClient/SpellDuration.dbc
  SpellItemEnchantment.dbc   base=  2656 custom= 98 added= 98 merged=  0 total=  2754   <- input/stock/DBFilesClient/SpellItemEnchantment.dbc
  GemProperties.dbc          base=   609 custom= 98 added= 98 merged=  0 total=   707   <- input/stock/DBFilesClient/GemProperties.dbc
  ItemExtendedCost.dbc       base=   972 custom= 21 added= 21 merged=  0 total=   993   <- input/stock/DBFilesClient/ItemExtendedCost.dbc
  SkillLineAbility.dbc       base= 10229 custom=  1 added=  1 merged=  0 total= 10230   <- input/custom/DBFilesClient/SkillLineAbility.dbc
  QuestSort.dbc              base=    38 custom=  1 added=  1 merged=  0 total=    39   <- input/stock/DBFilesClient/QuestSort.dbc
  Item.dbc                   base= 46149 custom=331 added=331 merged=  0 total= 46480   <- input/custom/DBFilesClient/Item.dbc
  ItemDisplayInfo.dbc        base= 58034 custom= 29 added= 29 merged=  0 total= 58063   <- input/custom/DBFilesClient/ItemDisplayInfo.dbc
  validated ItemDisplayInfo icons in staging/
DONE. staging/ is ready to pack into output/patch-Z.MPQ.
```

(Counts vary depending on what patches are already on top of your client.)

### Build flow summary

`build_patch.py` has two modes:

* `customonly` writes DBCs containing only the rows in `definitions/*.json`.
  Use this for inspecting generated rows. Do not ship it as a client patch -
  it would replace full client DBCs with Black Rose-only files.
* `merge` combines `input/stock/` + `input/custom/` + `definitions/*.json`
  into a fully patched `staging/` tree. This is the distributable build.

During `merge`, normal rows are upserted by `ID`. Rows with `_merge: true`
only override the fields present in JSON, which is useful for tweaking stock
rows without zeroing fields we do not manage.

### 4. Pack into an MPQ

The packer is not yet wired into `build_patch.py`; for now, pack by hand.
Final archive should land at `tools/clientpatch/output/patch-Z.MPQ`.

Open Ladik's MPQ Editor and create a new MPQ:

* New MPQ: `tools/clientpatch/output/patch-Z.MPQ`
* Format: **MPQ format v1** (3.3.5a-compatible)
* Hash table size: at least 8192 (the worgoblin tree contributes ~6.5k files)
* Add the **contents** of the `staging/` folder, preserving directory
  structure, so the files end up rooted at the in-MPQ paths:
  ```
  DBFilesClient\Spell.dbc                      (+ the other 8 merged DBCs)
  DBFilesClient\ChrRaces.dbc                   (+ 25 other passthrough DBCs)
  Character\Worgen\Male\WorgenMale.M2          (+ ~1400 other model files)
  Interface\Icons\INV_BR_Misc_BlackMiasma.blp  (+ 28 other Black Rose icons)
  Interface\Icons\ability_racial_darkflight.blp (+ 11 worgoblin racial icons)
  Interface\GLUES\CHARACTERCREATE\...          (race-select UI)
  Sound\Creature\Worgen\...                    (race vocal UI)
  ```

Save and close.

If you would rather script it, build StormLib and use its
`MPQAddFile` / `smpq` CLI; the `staging/` layout already matches the
in-MPQ virtual paths. Pipeline-integrated packing is the next planned
step here.

### 5. Deploy

Drop the resulting `patch-Z.MPQ` into the client's `WoW/Data/` folder. The
client loads `patch-*.MPQ` archives alphabetically; `Z` sorts last so it
overrides everything else.

If an existing custom patch is locked by the client or an MPQ editor, close
that process before replacing it. For a quick local test, you can temporarily
deploy the new archive under a later-sorting name such as `patch-zz.mpq`;
remove the older duplicate once the lock is gone so you do not keep stale
patches around.

For a locale-scoped variant put it at `WoW/Data/enUS/patch-enUS-Z.MPQ`
instead. Both work for 3.3.5a.

Then:

1. Delete (or rename) `WoW/Cache/` so the client re-fetches item and quest
   data from the server. The `Cache/WDB/<locale>/` files in particular
   stash item, quest, and creature info.
2. Restart the client and log in.

## Verifying the patch is loaded

In-game:

* `/script DEFAULT_CHAT_FRAME:AddMessage(GetSpellInfo(900900))` should print
  `Power of the Black Rose`. If it prints nothing, `Spell.dbc` is not
  loading.
* `/script DEFAULT_CHAT_FRAME:AddMessage(GetSpellInfo(900903))` should print
  `Rurik's Death Mobile`. Same check, different spell.
* Hover **The Black Rose** trinket: the green `Use:` line should match the
  description we wrote.
* Add or hover **Black Miasma**: it should use
  `Interface\Icons\INV_BR_Misc_BlackMiasma.blp`. If it is a question mark,
  check that the packed MPQ contains both `DBFilesClient\Item.dbc` and
  `DBFilesClient\ItemDisplayInfo.dbc`, not just the BLP icon files.
* Hover any **Klug Ribbon** before socketing: tooltip should show
  `+N intellect` from the gem properties + enchantment join.
* Socket a Klug Ribbon into The Black Rose: the item tooltip should grow a
  socket bonus line `+N intellect`.
* Use **Reins of Rurik's Death Mobile** - the spell appears in the mount UI
  under Companions/Mounts as `Rurik's Death Mobile`, and casting it spawns
  the Mechano-Hog motorcycle model the client already has. If the mount
  appears but is named "Mekgineer's Chopper" or "Mechano-Hog", the client
  patch is not loading. If the mount UI says `Rurik's Death Mobile` but
  casting does nothing, the SQL migration `2026_05_22_06_*.sql` did not
  run (no display ID set on the server side).

If a tooltip is wrong but `GetSpellInfo` works, your row data is wrong rather
than the patch not loading.

## Updating the row data

There are two sources of truth, depending on which DBC:

* **Generated rows (spells, durations, enchants, gem props, ext costs,
  skill line, quest sort).** `definitions/_generate.py` is the source
  of truth; re-run it whenever the formulas change:

  ```bash
  cd tools/clientpatch/definitions
  python3 _generate.py
  ```

* **Item rows (`Item.dbc`).** `item_template` is the source of truth -
  the SQL migration in `modules/mod-blackrose/data/sql/db-world/`. After
  applying SQL changes, dump fresh rows from the live DB:

  ```bash
  python3 tools/clientpatch/dump_items.py
  ```

  This connects to MySQL using `MYSQL_HOST` / `MYSQL_USER` /
  `MYSQL_PASSWORD` / `MYSQL_DB` env vars (defaults: `127.0.0.1` /
  `acore` / `acore` / `acore_world`) and writes
  `definitions/item.json` covering every item with `entry` in
  `[900100, 901199]`.

Then rebuild the patch with `python3 build_patch.py merge` from the
`tools/clientpatch/` directory.

For one-off hand edits, just edit the JSON directly. Re-running the
generators will overwrite hand edits.

## Notes and gotchas

* **MPQ format must be v1** for 3.3.5a. Format v2/v3/v4 will not load.
* **Field ordering** in our schemas matches AzerothCore's `*_dbc` SQL
  tables exactly, which the AC core asserts equals the binary file layout
  (see `src/server/shared/DataStores/DBCDatabaseLoader.cpp:118`). The same
  alignment is used by the binary writer here.
* **Locale strings** for descriptions use the enUS slot only; other locale
  slots remain empty. `Name_Lang_Mask` and `Description_Lang_Mask` are set to
  `1` to mark the enUS slot as populated, matching the SQL.
* **Server SQL must already be applied.** The client patch only adds
  tooltip data and item type metadata; gameplay still goes through the
  server. Apply the module's SQL (`2026_05_22_00_blackrose_data.sql` and
  `2026_05_22_01_blackrose_dbc.sql`) and restart the worldserver before
  testing.
* **Cache must be cleared.** Custom item/spell IDs that the client has
  already cached as `Unknown` will stay broken until `WoW/Cache/` is wiped.
* **`Item.dbc` matters for both icons and right-click.** Without the custom
  item rows, the client can keep using stale stock display IDs and cannot
  classify custom equippables locally. That can render question-mark icons
  even when the BLP files are present, and can make trinkets send
  `CMSG_USE_ITEM` instead of `CMSG_AUTOEQUIP_ITEM`. Re-run `dump_items.py`,
  `build_patch.py merge`, and repack the MPQ any time you add/edit items in
  the SQL migration.
* **`ItemDisplayInfo.dbc` matters for icon basenames.** This DBC maps the
  `DisplayInfoID` from `Item.dbc` / `item_template.displayid` to
  `InventoryIcon_1`. The value must be a basename like
  `INV_BR_Misc_BlackMiasma`, not a path and not a `.blp` filename.
