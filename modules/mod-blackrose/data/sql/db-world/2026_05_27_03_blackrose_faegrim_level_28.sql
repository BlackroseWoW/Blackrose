-- ============================================================================
-- Black Rose: Faegrim level + HP retune
--
-- Player feedback: level-30 / 7k HP felt right for a mid-tier elite, but the
-- group is hitting him at lower brackets and wants the fight playable a bit
-- earlier. Drop the level to 28 while keeping HP fixed at 7,000.
--
-- HealthModifier math: creature_classlevelstats.basehp0 at level 28 / class 1
-- is 853, so 7000 / 853 = 8.2122... -> use 8.21 (rounds to ~6,999.13, close
-- enough that the displayed HP is exactly 7k after AC's int truncation).
--
-- Spawnling level range rides down with him: was 26-27 against a level-30
-- boss, now 24-25 against a level-28 boss to preserve the same 3-4 level gap.
-- ============================================================================

SET @BR_BOSS         := 900200;
SET @BR_BOSS_ADD     := 900201;

UPDATE `creature_template`
   SET `minlevel`        = 28,
       `maxlevel`        = 28,
       `HealthModifier`  = 8.21         -- 8.21 * basehp0(853) = ~7000
 WHERE `entry` = @BR_BOSS;

UPDATE `creature_template`
   SET `minlevel` = 24,
       `maxlevel` = 25
 WHERE `entry` = @BR_BOSS_ADD;
