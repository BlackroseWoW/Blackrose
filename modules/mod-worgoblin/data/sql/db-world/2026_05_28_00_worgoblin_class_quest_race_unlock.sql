-- ============================================================================
-- Black Rose | mod-worgoblin: class-quest race-mask unlock for Worgen/Goblin
--
-- Vanilla AzerothCore ships a ton of race-themed class progression quests:
--
--   * Hunter "Taming the Beast" / "Training the Beast" line (lvl 10)
--     - one variant per starting race; each grants Tame Beast, Call Pet,
--       Revive Pet, Mend Pet, Feed Pet, Dismiss Pet via RewardSpell.
--   * Druid "Heeding the Call" / aquatic / great-bear-spirit chains
--   * Warlock demon summoning quests (Imp/Voidwalker/Succubus/Felhunter)
--   * Paladin Lay on Hands / Greater Blessings quests
--   * Priest racial-spell quests (Shadowform, etc.)
--   * Mage racial Polymorph-variant quests
--   * Death Knight "Where Kings Walk" / "An End to All Things..." transition
--     out of the Scarlet Enclave instance, and the lvl-55 "A Special Surprise"
--     execution scene (handled in its own migration: ..._01_..._special_surprise).
--
-- Each of these has a hard `quest_template.AllowableRaces` mask of a *single*
-- vanilla race. Worgen (mask 2048) and Goblin (mask 256) never appear, so a
-- Goblin Hunter can't accept ANY of the Taming the Beast variants, never
-- learns Mend Pet, and is stuck without a pet.
--
-- Strategy: rather than ship 12 + 12 hand-authored race variants of every
-- class quest, expand AllowableRaces on existing class-quests to include
-- Worgen / Goblin where faction-appropriate. The quests themselves work the
-- same; the Worgen Hunter just hikes to Kharanos and talks to Grif Wildheart.
--
-- The filter is intentionally narrow: only quests with a non-zero
-- `quest_template_addon.AllowableClasses` (= explicitly class-restricted)
-- get touched. Generic race-flavor quests (e.g. "Cellblock Riot" Dwarf-only
-- starting zone bits) are left alone.
--
-- Race mask reference:
--   Human=1   Orc=2   Dwarf=4   NightElf=8   Undead=16   Tauren=32
--   Gnome=64  Troll=128   Goblin=256   BloodElf=512   Draenei=1024   Worgen=2048
--   Alliance vanilla mask  = 1 + 4 + 8 + 64 + 1024 = 1101
--   Horde    vanilla mask  = 2 + 16 + 32 + 128 + 512 = 690
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. Class quests gated to pure-Alliance race(s) -> grant Worgen access.
-- ---------------------------------------------------------------------------
UPDATE `quest_template` qt
INNER JOIN `quest_template_addon` qta ON qt.`ID` = qta.`ID`
SET qt.`AllowableRaces` = qt.`AllowableRaces` | 2048
WHERE qta.`AllowableClasses` <> 0
  AND qt.`AllowableRaces` > 0
  AND (qt.`AllowableRaces` & 1101) <> 0          -- at least one Alliance vanilla race
  AND (qt.`AllowableRaces` & 690)  = 0           -- no Horde races
  AND (qt.`AllowableRaces` & 2048) = 0;          -- not already Worgen

-- ---------------------------------------------------------------------------
-- 2. Class quests gated to pure-Horde race(s) -> grant Goblin access.
-- ---------------------------------------------------------------------------
UPDATE `quest_template` qt
INNER JOIN `quest_template_addon` qta ON qt.`ID` = qta.`ID`
SET qt.`AllowableRaces` = qt.`AllowableRaces` | 256
WHERE qta.`AllowableClasses` <> 0
  AND qt.`AllowableRaces` > 0
  AND (qt.`AllowableRaces` & 690)  <> 0          -- at least one Horde vanilla race
  AND (qt.`AllowableRaces` & 1101) = 0           -- no Alliance races
  AND (qt.`AllowableRaces` & 256)  = 0;          -- not already Goblin

-- ---------------------------------------------------------------------------
-- 3. Cross-faction class quests (mask spans both factions, like some DK
--    Scarlet Enclave intermediate quests) -> grant both Worgen and Goblin.
-- ---------------------------------------------------------------------------
UPDATE `quest_template` qt
INNER JOIN `quest_template_addon` qta ON qt.`ID` = qta.`ID`
SET qt.`AllowableRaces` = qt.`AllowableRaces` | 2304
WHERE qta.`AllowableClasses` <> 0
  AND qt.`AllowableRaces` > 0
  AND (qt.`AllowableRaces` & 1101) <> 0
  AND (qt.`AllowableRaces` & 690)  <> 0
  AND (qt.`AllowableRaces` & 2304) <> 2304;

-- ---------------------------------------------------------------------------
-- 4. Targeted hot-fixes for known DK chain transitions that DON'T set
--    `quest_template_addon.AllowableClasses` (the gate is implicit via the
--    Scarlet Enclave phase) but still race-restrict in a way that locks out
--    Worgen / Goblin.
--
-- 13188 'Where Kings Walk'           : Alliance final transition -> Stormwind
-- 13189 'The Banshee Queen'          : Horde    final transition -> Undercity
--
-- 13189 doesn't exist in 3.3.5a base (the Horde-equivalent transition uses
-- the universally-available 'An End to All Things...' chain instead), but
-- guard against future schema drift with a NULL-safe IGNORE.
-- ---------------------------------------------------------------------------
UPDATE `quest_template`
SET `AllowableRaces` = `AllowableRaces` | 2048
WHERE `ID` = 13188                                  -- Where Kings Walk
  AND (`AllowableRaces` & 2048) = 0;
