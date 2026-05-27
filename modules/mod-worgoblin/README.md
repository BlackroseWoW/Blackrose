# mod-worgoblin

AzerothCore module that brings **Goblin** (race id `9`) and **Worgen** (race id
`12`) into a 3.3.5a WotLK realm as fully-playable races: character creation
sections, starting zones, starter gear, racial passives + actives, racial
languages, and the two Cata-era racial mount lines.

> **Upstream**: [benjymansy123/mod-worgoblin](https://github.com/benjymansy123/mod-worgoblin)
> (marked *no longer maintained*). This is the **Black Rose** fork. Outside of
> the model / texture assets, almost every server-side path has been rewritten
> for modern AzerothCore (new module layout, new SQL update format, new
> trainer / creature schema), and gameplay-level features such as racial
> spells, mounts, two-forms behaviour, and starting equipment - which shipped
> as TODO stubs upstream - now actually work.

---

## What it does

### Races

| race id | side | name   | starter map / position                | inn / hearth area              |
| ------- | ---- | ------ | ------------------------------------- | ------------------------------ |
| 9       | Horde     | Goblin | Durotar (map 1, ~(-246, -4428, 87))   | Razor Hill                     |
| 12      | Alliance  | Worgen | Kalimdor float-island (map 1, ~(9317, 20, 1213)) | Stormwind hearth on first login |

Both races can be chosen on the character-creation screen once the Black Rose
client patch (`Patch-X.mpq`) is in `Data/`. Class allow-lists, skin/face/hair
combinations, and starting outfits are wired through the DBC migrations below.

### Racial spells (server-side wiring)

The upstream module shipped the *skill lines* for Worgen (`789` "Racial -
Worgen") and Goblin (`790` "Racial - Goblin") but left the SkillLineAbility
rows and the `playercreateinfo_spell_custom` grants as commented-out TODOs.
The Black Rose port wires every racial that the bundled `Spell.dbc` already
defines:

| spell id | race          | name                                  | type            |
| -------- | ------------- | ------------------------------------- | --------------- |
| `68975`  | Worgen        | Viciousness (+1% crit)                | passive         |
| `68976`  | Worgen        | Aberration (-1% Nature/Shadow hit)    | passive         |
| `68978`  | Worgen        | Flayer (+Skinning, faster)            | passive         |
| `68992`  | Worgen        | Darkflight (sprint)                   | **active**      |
| `68995`  | Worgen male   | Two Forms (cosmetic toggle, male)     | **active**      |
| `68996`  | Worgen female | Two Forms (cosmetic toggle, female)   | **active**      |
| `69041`  | Goblin        | Rocket Barrage (single-target nuke)   | **active**      |
| `69042`  | Goblin        | Time is Money (+1% haste)             | passive         |
| `69044`  | Goblin        | Best Deals Anywhere (20% rep discount)| passive (C++)   |
| `69045`  | Goblin        | Better Living Through Chemistry       | passive (+Alch) |
| `69046`  | Goblin        | Pack Hobgoblin (mobile bank, 5/cd)    | **active**      |
| `69070`  | Goblin        | Rocket Jump (forward leap)            | **active**      |

Active racials are slotted on the default action bar at create time so new
characters can see and use them immediately. *Running Wild* (`87840`) is
intentionally omitted - we don't have the on-all-fours mount asset in the
client patch.

### Racial mounts

Goblin and Worgen each get an apprentice + a swift ground mount, gated by the
standard Riding skill (`762`) ranks so players still have to train Riding at
the regular vanilla trainers.

| spell id  | name                  | learned from item        | required skill        |
| --------- | --------------------- | ------------------------ | --------------------- |
| `87090`   | Goblin Trike          | `62461` Goblin Trike Key    | Apprentice Riding (75)  |
| `87091`   | Goblin Turbo-Trike    | `62462` Turbo-Trike Key     | Journeyman Riding (150) |
| `103195`  | Mountain Horse        | `73838` Mountain Horse      | Apprentice Riding (75)  |
| `103196`  | Swift Mountain Horse  | `73839` Swift Mountain Horse| Journeyman Riding (150) |

The mount keys are sold in-world by two race-gated vendors:

* **Kall Worthaton** (`Trike Dealer`) - Orgrimmar, `(2042.7, -4753.9, 29.4)`
* **Lorna Crowley** (`Stable Master`) - Stormwind, `(-8406.8, 683.4, 95.3)`

Both vendors use `CONDITION_RACE` so Goblins see Kall's stock + Worgen see
Lorna's stock; everyone else gets a polite refusal line on click.

### Two Forms gender fix (server-side C++)

`learnSkillRewardedSpells` auto-grants *both* gender-specific Two Forms
spells (`68995` male + `68996` female, each hard-coded to a single Human
display id) to every Worgen as `PLAYERSPELL_TEMPORARY` because both have
`AcquireMethod=2` SLA rows. `PlayerScript::OnPlayerLogin` removes the
gender-wrong temporary copy so each Worgen sees exactly one Two Forms entry
in the spellbook, and `OnPlayerFirstLogin` slots the correct variant on
action-bar button 11. Implementation is in `src/Worgoblin.cpp`.

### Languages

Goblin chars learn Common + Orcish + **Goblin Binary** (`907`). Worgen chars
learn Common + Orcish + **Darnassian** (`113`, via a one-off
`skillraceclassinfo_dbc` opt-in for the Worgen race mask).

---

## Repository layout

```
modules/mod-worgoblin/
├── src/
│   ├── Worgoblin.cpp          # PlayerScript + Rocket Barrage SpellScript
│   └── worgoblin_loader.cpp   # Addmod_worgoblinScripts entry point
├── data/sql/db-world/         # 28 auto-applied migrations (see breakdown below)
└── data/sql/supplementary/    # opt-in upstream content, NOT auto-applied
```

### Migration breakdown (`data/sql/db-world/`)

| date / id              | scope                                                                 |
| ---------------------- | --------------------------------------------------------------------- |
| `2026_05_26_00`        | Base data: race stats, totem models, starting zones, starter gear, action bars, racial skill assignments, achievement criteria, mount creature templates, mount key items |
| `2026_05_26_01_*_dbc`  | 17 server-side DBC mirrors: `chrraces`, `creaturedisplayinfo`, `creaturedisplayinfoextra`, `creaturemodeldata`, `faction`, `itemdisplayinfo`, `skillline`, `skilllineability`, `skillraceclassinfo`, `soundentries`, `spell` (mounts + racials), `summonproperties`, `talenttab`, `barbershopstyle`, `charstartoutfit`, `achievement`, `achievement_criteria` |
| `2026_05_26_02`        | Common / Orcish / Goblin-Binary language skill grants                  |
| `2026_05_26_03`        | Darnassian opt-in for Worgen                                           |
| `2026_05_26_04`        | Remove 49 orphan custom item IDs left over from upstream's starter gear (Black Rose reuses the matching vanilla items 1:1 instead) |
| `2026_05_26_05`        | Darkflight + Two Forms SLA bind; `playercreateinfo_spell_custom` grants for every racial; action-bar slot defaults |
| `2026_05_26_06`        | Male-variant Two Forms SLA                                             |
| `2026_05_26_07`        | Flip Two Forms SLA `AcquireMethod` so the gender-correct copy doesn't get hidden as a side-effect of the dedup |
| `2026_05_26_08`        | Restore the female-variant Two Forms SLA row that the previous fix had inadvertently stripped |
| `2026_05_27_00`        | Mount SLA: add `skilllineability_dbc` rows for the 4 mount spells on skill 762 ("Riding") so the mounts actually appear in the spellbook's Mounts tab once learned; add the missing `skillline_dbc` mirror for 762 |
| `2026_05_27_01`        | In-world mount vendors (Kall Worthaton, Lorna Crowley) with race-gated gossip; spawns in Orgrimmar + Stormwind |
| `2026_05_27_03`        | Strip the retail-Cata `SPELL_AURA_MOD_FLIGHT_SPEED_MOUNTED` (aura 207) effect from all 4 mount spells - on WotLK these are ground-only and the lingering flight aura was making apprentice and journeyman versions feel identically fast |

---

## Server-side

C++ side is two files compiled into the worldserver:

* `src/Worgoblin.cpp`
  * `class worgoblin : public PlayerScript`
    * `OnPlayerLogin` - login banner (configurable via `Announce.enable`),
      Two Forms gender dedup.
    * `OnPlayerFirstLogin` - Two Forms action-bar slot (button 11).
    * `OnPlayerGetReputationPriceDiscount` - Goblin Best Deals Anywhere
      (`69044`): multiplies vendor rep price by `0.8` (20% discount).
  * `class spell_rocket_barrage : public SpellScript` - rebuilds the damage
    formula for Goblin Rocket Barrage (`69041`) as
    `level*2 + 0.429*spellpower + 0.25*AP` (uses ranged AP for hunters,
    melee for everyone else) and pushes it onto the spell effect.
* `src/worgoblin_loader.cpp` - defines `Addmod_worgoblinScripts()`, the entry
  point AzerothCore's CMake module discovery calls.

SQL side is the 28 migrations listed above, auto-applied by AC's module
updater (`UpdateFetcher::Update` recursively scans
`modules/<name>/data/sql/db-*/`). No manual `mysql` invocations needed; just
build and restart the worldserver.

## Client-side

The module's client-side payload was lifted out of the upstream's nested
`data/patch/` folder and is now owned by the shared Black Rose clientpatch
pipeline:

* `tools/clientpatch/input/custom/DBFilesClient/*.dbc` - 30+ pre-patched
  3.3.5a DBCs covering character creation, racial skills, starter outfit
  rows, item display info, mount creature data, etc.
* `tools/clientpatch/input/custom/{Character,Creature,Interface,Sound,Spells,Textures,World}/`
  - ~6,500 model / texture / skin / lua / ogg assets the racial models
  reference (Worgen male+female, Goblin male+female, mount M2s, racial
  spell icons, gossip strings, ...).
* `tools/clientpatch/definitions/skilllineability.json` - 4 mount-SLA rows
  (IDs 22000-22003) so the rebuilt `SkillLineAbility.dbc` carries the same
  entries the server-side migration adds.

Build the patch with:

```bash
cd tools/clientpatch
python3 build_patch.py merge          # custom → staging/ + overlay merge
# then pack staging/ into Patch-X.mpq using mpq_replace or your MPQ editor
```

See [`tools/clientpatch/README.md`](../../tools/clientpatch/README.md#input-layers)
for the full layer / overlay rules.

---

## Optional / opt-in content (`data/sql/supplementary/`)

Three legacy files survive from the upstream module:

* `dk-quests.sql` - Death Knight starter quest variant.
* `optional-class-quests.sql` - per-class quest tweaks.
* `optional-class-trainers.sql` - extra class trainer spawns.

These are **not** under `db-world/` so AC's auto-updater never touches them.
They also still use the pre-modern AC schema (`creature_template.modelid1..4`,
`trainer_type`, `mechanic_immune_mask`, etc.) and will reject on apply unless
ported. The upstream `optional-mount-vendor.sql` was dropped during the
rewrite - its content is now covered by the modern, schema-correct
`2026_05_27_01_worgoblin_mount_vendor.sql` migration in `db-world/`.

---

## Installation

The module is already wired into the Black Rose tree:

* Server-side source + SQL in `modules/mod-worgoblin/` (this folder).
* `.gitignore` carves out an exception so the whole tree is tracked.
* Client-side assets live under `tools/clientpatch/input/custom/` and are
  picked up automatically by `build_patch.py` - no code change needed to
  add new module assets, just drop them into that tree.

Static (default) AC builds discover the module automatically. To skip it,
pass `-DDISABLED_AC_MODULES="mod-worgoblin"` on the CMake line.

The only post-install steps are:

1. Build + install the worldserver normally (`make -j$(nproc) && make install`).
2. Start the worldserver - AC's module updater auto-applies the SQL.
3. Rebuild `Patch-X.mpq` (`tools/clientpatch/build_patch.py`) and drop it in
   the client `Data/` folder.
4. Clear the client's `Cache/WDB/` folder so item / NPC tooltips refresh.

---

## What changed vs the upstream module

The Black Rose port is functionally a rewrite. High-level diff:

### Structure / build
* Folder renamed `mod-worgoblin-master/` → `mod-worgoblin/` so AC's discovery
  hits the expected loader name `Addmod_worgoblinScripts`.
* Loader split out of a header: `worgoblin_loader.cpp` defines the entry
  point (was previously inline in a header that only worked because exactly
  one `.cpp` included it - fragile).
* `data/sql/db-world/worgoblin.sql` flattened into the modern
  `YYYY_MM_DD_NN_worgoblin_<scope>.sql` convention; the 17 nested
  `workflow/*_dbc.sql` files were promoted up one level with unique
  filenames (AC's updater rejects duplicates).

### Client pipeline
* Upstream's `data/patch/` tree (~6,500 client-side DBCs + assets) was
  moved out of the module into `tools/clientpatch/input/custom/` so the
  Black Rose clientpatch pipeline owns all client data uniformly. The
  module itself is now pure C++ + SQL.
* Manual drop-DBCs-into-`Data/` step (upstream README §2) is gone.

### Gameplay - racial spells
* Every Worgen and Goblin racial that ships in the bundled `Spell.dbc` is
  now actually granted to new characters via `playercreateinfo_spell_custom`
  and slotted on the action bar via `playercreateinfo_action`. Upstream
  shipped these as commented-out TODOs.
* Two Forms (`68995`/`68996`) gender behaviour rebuilt server-side via a
  `PlayerScript` hook so each Worgen ends up with exactly one variant in
  the spellbook and on the action bar (upstream granted both, leaving
  every Worgen with two confused-looking buttons that transformed them
  into the wrong-gender Human).

### Gameplay - mounts
* SkillLineAbility rows added for all four racial mounts so they appear in
  the spellbook's Mounts tab once the player learns them via the key item
  (upstream learned the spell but the spell never rendered).
* Stripped the leaked-over Cata flight-speed aura from the mount spells so
  apprentice (+60%) and journeyman (+100%) variants finally feel different
  from each other on the ground.
* Added two in-world race-gated vendors (Orgrimmar + Stormwind) so the
  mount keys are obtainable without GM commands. The optional vendor SQL
  upstream shipped was Goblin-only and used the pre-modern schema; this
  rewrite covers both races and uses the current `trainer` /
  `creature_default_trainer` / `npc_vendor` tables.

### Gameplay - starting equipment
* `charstartoutfit_dbc` rerouted to use vanilla item IDs rather than the
  49 custom items upstream shipped (which had no client-side icon /
  display info entries, so they all rendered as "?"). The orphan custom
  item rows are removed by `2026_05_26_04`.

### Gameplay - languages
* Goblin / Worgen language skills are explicitly assigned via
  `playercreateinfo_skills` and `skillraceclassinfo_dbc` so /say + chat
  bubbles work for cross-faction Worgen / Goblin (upstream chars spawned
  with `0` languages and got "no language" errors on every chat attempt).

---

## Credits

* Original module: mthsena, Helias, yuan2105, Tanados, Trimitor#3873, and the
  rest of the upstream `benjymansy123/mod-worgoblin` contributors (see
  `LICENSE` for the full list).
* Worgen / Goblin model + texture extraction: upstream module assets.
* Black Rose rewrite: in-tree, see `git log -- modules/mod-worgoblin`.

## License

GPLv3, same as upstream. See `LICENSE`.
