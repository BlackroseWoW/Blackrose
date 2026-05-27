# mod-blackrose

The "house module" for the Black Rose realm. Owns all of the custom server
content that isn't a separate concept:

* The custom Black Rose questline.
* Rosy vendor content + Bag of the Black Rose upgrades.
* The Black Rose trinket.
* The first red / yellow Black Rose gem systems.
* **Faegrim, the Putrid Husk** (entry `900200`) - mid-tier elite at Fire Scar
  Shrine. Spawns Putrid Spawnlings (`900201`) for group pressure. See the
  `2026_05_23_*` / `2026_05_24_*` / `2026_05_27_*` migrations for the boss's
  SmartAI script, immunity table, and tuning history.
* **Rurik's Death Mobile** (spell `900903`) - custom mount used by the
  Black Rose Mauler item. Standard ground-mount attributes: 1.5s cast,
  +100% speed, not usable in combat, drops on damage / dismount.

Build with modules enabled, apply the module SQL updates, restart worldserver,
and clear the WoW client cache before validating item names and tooltips.

## Client DBC Patch

The server module provides the custom rows used by worldserver. For full client
tooltip display, the client patch must also include:

- Spell `900900` with the green trinket `Use:` text.
- The 20-second duration row for spell `900900`.
- Black Rose `SpellItemEnchantment` rows for all Ribbon/Mist socket bonuses.
- Black Rose `GemProperties` rows for all Ribbon/Mist gem items.

## Configuration

Track `conf/BlackRose.conf.dist` in git. The real `BlackRose.conf` is generated
or copied into the server config directory for local use and should stay
untracked.

## Contribution Helpers

- `pull_request_template.md` documents the expected PR summary and test plan.
- `.git_commit_template.txt` follows the repository Conventional Commits style.
- `setup_git_commit_template.sh` can set the local git commit template for this
  repository.
