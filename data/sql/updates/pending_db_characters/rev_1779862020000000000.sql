-- Backfill: swap Two Forms 68996 -> 68995 for existing male Worgen.
--
-- Two Forms is split into a male variant (68995, transforms into
-- CreatureDisplayInfo 20707 / Human male) and a female variant
-- (68996, transforms into 20708 / Human female). The previous
-- backfill granted 68996 to every existing Worgen regardless of
-- gender, so male Worgen turned into a human female model.
--
-- This migration:
--   * Removes 68996 from male Worgen (race 12, gender 0) and grants
--     68995 instead, both in character_spell and any matching
--     character_action button.
--   * Leaves female Worgen and Goblin characters untouched.

-- character_spell: drop the wrong-gender entry first, then insert the right one.
DELETE FROM `character_spell` WHERE `spell` = 68995 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `race` = 12 AND `gender` = 0);
DELETE FROM `character_spell` WHERE `spell` = 68996 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `race` = 12 AND `gender` = 0);
INSERT INTO `character_spell` (`guid`, `spell`, `specMask`)
SELECT `guid`, 68995, 255 FROM `characters` WHERE `race` = 12 AND `gender` = 0;

-- character_action: swap any action-bar slot that points at 68996 over to 68995 for male Worgen.
DELETE FROM `character_action` WHERE `action` = 68995 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `race` = 12 AND `gender` = 0);
UPDATE `character_action` SET `action` = 68995 WHERE `action` = 68996 AND `guid` IN (SELECT `guid` FROM `characters` WHERE `race` = 12 AND `gender` = 0);
