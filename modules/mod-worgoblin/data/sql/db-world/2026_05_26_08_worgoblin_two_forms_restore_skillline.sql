-- mod-worgoblin: restore AcquireMethod=2 on the Two Forms SLA rows so the
-- client puts them in the Worgen Racial spellbook tab.
--
-- Migration 2026_05_26_07_* set AcquireMethod=0 to stop the server from
-- auto-granting both gender variants via Player::learnSkillRewardedSpells.
-- That worked server-side but the client also uses AcquireMethod=2 to
-- decide whether a spell appears in the racial tab -- with 0, the spell
-- vanished from the spellbook entirely even though it was learned.
--
-- Putting the bindings back to AcquireMethod=2 restores the spellbook tab.
-- Filtering the wrong-gender variant now happens in C++ (worgoblin::
-- OnPlayerLogin) by calling Player::removeSpell with onlyTemporary=true on
-- the variant that doesn't match the player's gender. The auto-learn always
-- inserts both as PLAYERSPELL_TEMPORARY, so the targeted remove cleans the
-- in-memory copy without touching any persisted DB rows.

DELETE FROM `skilllineability_dbc` WHERE `ID` IN (21990, 21991);
INSERT INTO `skilllineability_dbc`
    (`ID`, `SkillLine`, `Spell`, `RaceMask`, `ClassMask`, `ExcludeRace`, `ExcludeClass`,
     `MinSkillLineRank`, `SupercededBySpell`, `AcquireMethod`,
     `TrivialSkillLineRankHigh`, `TrivialSkillLineRankLow`,
     `CharacterPoints_1`, `CharacterPoints_2`)
VALUES
    (21990, 789, 68996, 2048, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0),
    (21991, 789, 68995, 2048, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0);
