--
-- Make SKILL_LANG_DARNASSIAN (113) legal for Worgen (race 12).
--
-- 2026_05_26_02_worgoblin_language_skills.sql inserts (2048, 0, 113) into
-- playercreateinfo_skills, but vanilla SkillRaceClassInfo.dbc only ships row 56
-- with RaceMask=8 (NightElf). On Player::Create the LearnDefaultSkill call at
-- Player.cpp:11886 bails because GetSkillRaceClassInfo(113, 12, anyclass)
-- returns nullptr (DBCStores.cpp:895), so a fresh Worgen never picks the skill
-- up. Worse, for existing Worgens that were backfilled via
-- pending_db_characters/rev_1779837557859024191.sql, _LoadSkills at
-- PlayerStorage.cpp:5485 -> Player.cpp:13762 flags skill 113 as
-- "invalid for the race/class combination" and marks it SKILL_DELETED, which
-- _SaveSkills then nukes from character_skills on next logout.
--
-- Adding a new SkillRaceClassInfo overlay row keyed at ID 973 (just past
-- skillraceclassinfo_dbc.sql's last ID 972 for the Goblin racial) extends
-- Darnassian to Worgen without disturbing the NightElf entry that still lives
-- in the binary DBC. We mirror the column shape used by the existing language
-- rows (rows 40 and 48 in 2026_05_26_01_worgoblin_skillraceclassinfo_dbc.sql)
-- so Flags=128 / MinLevel=0 / SkillTierID=0 / SkillCostIndex=0.
--
-- ClassMask=1535 matches every player class (1+2+4+8+16+32+64+128+256+1024)
-- which is the same blanket the vanilla language rows use - languages are not
-- class-gated.
--
DELETE FROM `skillraceclassinfo_dbc` WHERE `ID` = 973;
INSERT INTO `skillraceclassinfo_dbc` (`ID`, `SkillID`, `RaceMask`, `ClassMask`, `Flags`, `MinLevel`, `SkillTierID`, `SkillCostIndex`) VALUES
(973, 113, 2048, 1535, 128, 0, 0, 0);
