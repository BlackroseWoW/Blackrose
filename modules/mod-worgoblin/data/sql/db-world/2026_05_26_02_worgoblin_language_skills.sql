--
-- Goblin (race 9) and Worgen (race 12) chat language skills.
--
-- Without these rows, /say and /yell bounce with "You can not speak this
-- language" (LANG_NOT_LEARNED_LANGUAGE / Language.h:754). The chat handler
-- only accepts a language when Player::HasSkill(langDesc->skill_id) returns
-- true (src/server/game/Handlers/ChatHandler.cpp:94). The race never picks
-- the skill up because playercreateinfo_skills had no entry covering
-- raceMask 256 (Goblin) or 2048 (Worgen) for skill 98 (Common) or
-- 109 (Orcish).
--
-- Assignments mirror vanilla's two-language pattern (faction + flavor):
--
--   Goblin  - Orcish (109)        same as every original Horde race
--                                  (no LANG_GOBLIN_BINARY hookup exists
--                                  in 3.3.5a; lang_description in
--                                  ObjectMgr.cpp:251 leaves it skill 0)
--
--   Worgen  - Common (98)         the Gilnean tongue is a Common dialect
--           + Darnassian (113)    thematic nod to the Worgen-Druid lore
--                                  tie (Malfurion's circle taught Gilnean
--                                  survivors after the curse), matching
--                                  the way Tauren learn Taurahe alongside
--                                  Orcish.
--
-- LearnDefaultSkills (Player.cpp:11870) reads these at Player::Create,
-- so this only affects newly-created Goblin/Worgen characters. Existing
-- test characters get backfilled by the matching pending_db_characters
-- rev file.
--
DELETE FROM `playercreateinfo_skills`
  WHERE (`raceMask` = 256  AND `classMask` = 0 AND `skill` = 109)
     OR (`raceMask` = 2048 AND `classMask` = 0 AND `skill` IN (98, 113));

INSERT INTO `playercreateinfo_skills` (`raceMask`, `classMask`, `skill`, `rank`, `comment`) VALUES
(256,  0, 109, 0, 'Language: Orcish - Goblin'),
(2048, 0, 98,  0, 'Language: Common - Worgen'),
(2048, 0, 113, 0, 'Language: Darnassian - Worgen');
