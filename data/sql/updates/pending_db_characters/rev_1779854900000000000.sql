-- Backfill all Worgen and Goblin racials onto every existing character of the
-- corresponding race. New characters get them at creation via
-- modules/mod-worgoblin/data/sql/db-world/2026_05_26_05_worgoblin_darkflight_twoforms.sql.
--
-- Worgen racials (race 12): Viciousness, Aberration, Flayer, Darkflight, Two Forms
-- Goblin racials (race  9): Rocket Barrage, Time is Money, Best Deals Anywhere,
--                            Better Living Through Chemistry, Pack Hobgoblin, Rocket Jump
--
-- specMask = 255 marks each spell as known across all talent specs.

-- ---- Worgen ----
DELETE FROM `character_spell` WHERE `spell` = 68975 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `race` = 12);
INSERT INTO `character_spell` (`guid`, `spell`, `specMask`)
SELECT `characters`.`guid`, 68975, 255 FROM `characters` WHERE `characters`.`race` = 12;

DELETE FROM `character_spell` WHERE `spell` = 68976 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `race` = 12);
INSERT INTO `character_spell` (`guid`, `spell`, `specMask`)
SELECT `characters`.`guid`, 68976, 255 FROM `characters` WHERE `characters`.`race` = 12;

DELETE FROM `character_spell` WHERE `spell` = 68978 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `race` = 12);
INSERT INTO `character_spell` (`guid`, `spell`, `specMask`)
SELECT `characters`.`guid`, 68978, 255 FROM `characters` WHERE `characters`.`race` = 12;

DELETE FROM `character_spell` WHERE `spell` = 68992 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `race` = 12);
INSERT INTO `character_spell` (`guid`, `spell`, `specMask`)
SELECT `characters`.`guid`, 68992, 255 FROM `characters` WHERE `characters`.`race` = 12;

DELETE FROM `character_spell` WHERE `spell` = 68996 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `race` = 12);
INSERT INTO `character_spell` (`guid`, `spell`, `specMask`)
SELECT `characters`.`guid`, 68996, 255 FROM `characters` WHERE `characters`.`race` = 12;

-- ---- Goblin ----
DELETE FROM `character_spell` WHERE `spell` = 69041 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `race` = 9);
INSERT INTO `character_spell` (`guid`, `spell`, `specMask`)
SELECT `characters`.`guid`, 69041, 255 FROM `characters` WHERE `characters`.`race` = 9;

DELETE FROM `character_spell` WHERE `spell` = 69042 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `race` = 9);
INSERT INTO `character_spell` (`guid`, `spell`, `specMask`)
SELECT `characters`.`guid`, 69042, 255 FROM `characters` WHERE `characters`.`race` = 9;

DELETE FROM `character_spell` WHERE `spell` = 69044 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `race` = 9);
INSERT INTO `character_spell` (`guid`, `spell`, `specMask`)
SELECT `characters`.`guid`, 69044, 255 FROM `characters` WHERE `characters`.`race` = 9;

DELETE FROM `character_spell` WHERE `spell` = 69045 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `race` = 9);
INSERT INTO `character_spell` (`guid`, `spell`, `specMask`)
SELECT `characters`.`guid`, 69045, 255 FROM `characters` WHERE `characters`.`race` = 9;

DELETE FROM `character_spell` WHERE `spell` = 69046 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `race` = 9);
INSERT INTO `character_spell` (`guid`, `spell`, `specMask`)
SELECT `characters`.`guid`, 69046, 255 FROM `characters` WHERE `characters`.`race` = 9;

DELETE FROM `character_spell` WHERE `spell` = 69070 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `race` = 9);
INSERT INTO `character_spell` (`guid`, `spell`, `specMask`)
SELECT `characters`.`guid`, 69070, 255 FROM `characters` WHERE `characters`.`race` = 9;
