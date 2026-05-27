-- mod-worgoblin: Two Forms (Worgen <-> Human) is split across two spells:
--   * 68995 -- transforms into Human MALE   (CreatureDisplayInfo 20707)
--   * 68996 -- transforms into Human FEMALE (CreatureDisplayInfo 20708)
--
-- The previous migration (2026_05_26_05_*) granted 68996 to every Worgen,
-- which meant male Worgen turned into a human female model. This migration
-- corrects that:
--
--   * Adds a SkillLineAbility binding for 68995 so the male variant can
--     appear in the spellbook (mirror of 21990 for 68996).
--   * Removes 68996 from playercreateinfo_spell_custom and the Two Forms
--     row from playercreateinfo_action -- gender-aware granting is now
--     handled in C++ (worgoblin::OnPlayerCreate) since playercreateinfo_*
--     tables can't filter by gender.
--
-- A client-side SkillLineAbility.dbc entry mirroring this is patched into
-- Patch-X.mpq separately.

-- -------------------------------------------------------------------------
-- 1. SkillLineAbility entry for Two Forms (male variant, 68995)
--    Skill 789 = "Racial - Worgen". 21991 is the first ID free in both the
--    server overlay and the client SkillLineAbility.dbc (21985-21990 are
--    already allocated; 21989 is the client's Goblin Rocket Barrage row).
-- -------------------------------------------------------------------------
DELETE FROM `skilllineability_dbc` WHERE `ID` = 21991;
INSERT INTO `skilllineability_dbc`
    (`ID`, `SkillLine`, `Spell`, `RaceMask`, `ClassMask`, `ExcludeRace`, `ExcludeClass`,
     `MinSkillLineRank`, `SupercededBySpell`, `AcquireMethod`,
     `TrivialSkillLineRankHigh`, `TrivialSkillLineRankLow`,
     `CharacterPoints_1`, `CharacterPoints_2`)
VALUES
    (21991, 789, 68995, 2048, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0);

-- -------------------------------------------------------------------------
-- 2. Stop granting 68996 unconditionally to new Worgen. The mod's
--    PlayerScript::OnPlayerCreate hook now picks 68995 (male) or 68996
--    (female) based on Player::getGender().
-- -------------------------------------------------------------------------
DELETE FROM `playercreateinfo_spell_custom`
 WHERE `racemask` = 2048 AND `Spell` = 68996;

-- -------------------------------------------------------------------------
-- 3. Remove the Two Forms action-bar default. The C++ hook adds the
--    correct gendered spell to slot 11 at creation time.
-- -------------------------------------------------------------------------
DELETE FROM `playercreateinfo_action`
 WHERE `race` = 12 AND `action` = 68996;
