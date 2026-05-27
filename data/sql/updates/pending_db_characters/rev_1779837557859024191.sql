--
-- Backfill chat language skills for already-created Goblin (race 9) and
-- Worgen (race 12) characters. The matching playercreateinfo_skills rows
-- in modules/mod-worgoblin/data/sql/db-world/2026_05_26_02_worgoblin_language_skills.sql
-- only fire at Player::Create (Player.cpp:11870 LearnDefaultSkills), so
-- any test character that existed before that migration ran has no
-- language skill and /say bounces with "You can not speak this language".
--
-- SetSkill for language-range skills always uses value=300, max=300
-- (Player.cpp:11894 case SKILL_RANGE_LANGUAGE), so DELETE+INSERT here
-- only ever rewrites the row with the exact bytes LearnDefaultSkills
-- would write. The DELETE is scoped to the (guid, skill) pairs we are
-- about to upsert, so any other skill rows on the same character
-- (proficiencies, gathering professions, etc.) are untouched.
--
DELETE FROM `character_skills` WHERE `skill` = 109 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `race` = 9);
INSERT INTO `character_skills` (`guid`, `skill`, `value`, `max`) SELECT `guid`, 109, 300, 300 FROM `characters` WHERE `race` = 9;
DELETE FROM `character_skills` WHERE `skill` = 98 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `race` = 12);
INSERT INTO `character_skills` (`guid`, `skill`, `value`, `max`) SELECT `guid`, 98, 300, 300 FROM `characters` WHERE `race` = 12;
DELETE FROM `character_skills` WHERE `skill` = 113 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `race` = 12);
INSERT INTO `character_skills` (`guid`, `skill`, `value`, `max`) SELECT `guid`, 113, 300, 300 FROM `characters` WHERE `race` = 12;
