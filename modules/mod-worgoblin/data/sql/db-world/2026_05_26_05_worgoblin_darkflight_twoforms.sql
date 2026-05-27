-- mod-worgoblin: wire up every Worgen and Goblin racial that ships in our
-- spell_dbc. The mod's data SQL granted the racial *skill lines* (789 / 790)
-- but the spells themselves were left as commented-out TODOs, so existing
-- characters had skill ranks but no usable abilities.
--
-- This migration:
--   * Adds a SkillLineAbility binding for Two Forms (68996). All other racials
--     already have entries in skilllineability_dbc.
--   * Grants every racial spell to new Worgen / Goblin characters via
--     playercreateinfo_spell_custom (raceMask 2048 = Worgen, 256 = Goblin).
--   * Puts the active racials on the default action bar so brand-new chars can
--     see and use them immediately.
--
-- Running Wild (87840) is intentionally omitted: that spell isn't in our
-- spell_dbc and the on-all-fours mount asset isn't in the client patch.

-- -------------------------------------------------------------------------
-- 1. SkillLineAbility entry for Two Forms (68996)
--    Skill 789 = "Racial - Worgen". Other Worgen passives + Darkflight already
--    have rows (IDs 21981-21984). 21990 is the next free ID in both the
--    client binary DBC and the server overlay.
-- -------------------------------------------------------------------------
DELETE FROM `skilllineability_dbc` WHERE `ID` = 21990;
INSERT INTO `skilllineability_dbc`
    (`ID`, `SkillLine`, `Spell`, `RaceMask`, `ClassMask`, `ExcludeRace`, `ExcludeClass`,
     `MinSkillLineRank`, `SupercededBySpell`, `AcquireMethod`,
     `TrivialSkillLineRankHigh`, `TrivialSkillLineRankLow`,
     `CharacterPoints_1`, `CharacterPoints_2`)
VALUES
    (21990, 789, 68996, 2048, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0);

-- -------------------------------------------------------------------------
-- 2. Grant every racial spell to new characters.
--    racemask=2048 = Worgen, racemask=256 = Goblin, classmask=0 = all classes.
-- -------------------------------------------------------------------------
DELETE FROM `playercreateinfo_spell_custom`
 WHERE (`racemask` = 2048 AND `Spell` IN (68975, 68976, 68978, 68992, 68996))
    OR (`racemask` = 256  AND `Spell` IN (69041, 69042, 69044, 69045, 69046, 69070));
INSERT INTO `playercreateinfo_spell_custom` (`racemask`, `classmask`, `Spell`, `Note`) VALUES
(2048, 0, 68975, 'Worgen Racial - Viciousness (+1% crit)'),
(2048, 0, 68976, 'Worgen Racial - Aberration (-1% Nature/Shadow hit)'),
(2048, 0, 68978, 'Worgen Racial - Flayer (+Skinning, faster)'),
(2048, 0, 68992, 'Worgen Racial - Darkflight (active sprint)'),
(2048, 0, 68996, 'Worgen Racial - Two Forms (cosmetic toggle)'),
(256,  0, 69041, 'Goblin Racial - Rocket Barrage (active fire dmg)'),
(256,  0, 69042, 'Goblin Racial - Time is Money (+1% haste)'),
(256,  0, 69044, 'Goblin Racial - Best Deals Anywhere (gold discount)'),
(256,  0, 69045, 'Goblin Racial - Better Living Through Chemistry (+Alchemy)'),
(256,  0, 69046, 'Goblin Racial - Pack Hobgoblin (mobile bank)'),
(256,  0, 69070, 'Goblin Racial - Rocket Jump (forward leap)');

-- -------------------------------------------------------------------------
-- 3. Put active racials on the action bar for new characters.
--    Passives don't need bar slots. Goblins already get Rocket Barrage / Jump
--    via the original data SQL on slots 9/10; this just adds Pack Hobgoblin
--    on slot 11 and the two Worgen actives on slots 10/11.
-- -------------------------------------------------------------------------
DELETE FROM `playercreateinfo_action`
 WHERE (`race` = 12 AND `action` IN (68992, 68996))
    OR (`race` = 9  AND `action` IN (69046));
INSERT INTO `playercreateinfo_action` (`race`, `class`, `button`, `action`, `type`) VALUES
-- Worgen Darkflight + Two Forms on slots 10/11 for every Worgen class
(12, 1,  10, 68992, 0), (12, 1,  11, 68996, 0),
(12, 3,  10, 68992, 0), (12, 3,  11, 68996, 0),
(12, 4,  10, 68992, 0), (12, 4,  11, 68996, 0),
(12, 5,  10, 68992, 0), (12, 5,  11, 68996, 0),
(12, 6,  10, 68992, 0), (12, 6,  11, 68996, 0),
(12, 8,  10, 68992, 0), (12, 8,  11, 68996, 0),
(12, 9,  10, 68992, 0), (12, 9,  11, 68996, 0),
(12, 11, 10, 68992, 0), (12, 11, 11, 68996, 0),
-- Goblin Pack Hobgoblin on slot 11 (Rocket Barrage already on 9, Rocket Jump on 10)
(9, 1, 11, 69046, 0),
(9, 3, 11, 69046, 0),
(9, 4, 11, 69046, 0),
(9, 5, 11, 69046, 0),
(9, 6, 11, 69046, 0),
(9, 7, 11, 69046, 0),
(9, 8, 11, 69046, 0),
(9, 9, 11, 69046, 0);
