-- mod-worgoblin: stop the server from auto-learning both Two Forms variants.
--
-- skilllineability_dbc rows 21990 (68996) and 21991 (68995) both carry
-- AcquireMethod=2 (SKILL_LINE_ABILITY_LEARNED_ON_SKILL_LEARN) and
-- RaceMask=2048. AzerothCore's Player::learnSkillRewardedSpells runs at
-- every login for the Worgen Racial skill (789) and auto-learns every
-- matching SLA row, so every Worgen ends up with BOTH spells in their
-- spellbook regardless of gender. The spells are tagged PLAYERSPELL_TEMPORARY
-- so they don't persist to character_spell, but they're still sent in
-- SMSG_INITIAL_SPELLS and show as two "Two Forms" rows in-game.
--
-- AcquireMethod=0 leaves the SLA binding intact (the spellbook tab assignment
-- and CheckSkillLearnedBySpell validation both still work) but tells the
-- server "do not auto-grant from skill". Gender-correct learning is handled
-- by worgoblin::OnPlayerFirstLogin (C++) for new characters; existing
-- characters already have the right entry in character_spell.

DELETE FROM `skilllineability_dbc` WHERE `ID` IN (21990, 21991);
INSERT INTO `skilllineability_dbc`
    (`ID`, `SkillLine`, `Spell`, `RaceMask`, `ClassMask`, `ExcludeRace`, `ExcludeClass`,
     `MinSkillLineRank`, `SupercededBySpell`, `AcquireMethod`,
     `TrivialSkillLineRankHigh`, `TrivialSkillLineRankLow`,
     `CharacterPoints_1`, `CharacterPoints_2`)
VALUES
    (21990, 789, 68996, 2048, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    (21991, 789, 68995, 2048, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
