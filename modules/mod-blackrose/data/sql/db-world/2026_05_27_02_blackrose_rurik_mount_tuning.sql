-- ============================================================================
-- Black Rose: Rurik's Death Mobile tuning pass
--
-- Three issues with spell 900903 as it currently ships:
--   1. Speed is +300% mount speed (EffectBasePoints_2 = 299, engine adds 1
--      -> +300%). That is faster than Cold Weather Flying and trivializes
--      ground travel for the level bracket this trinket targets. Bringing
--      it down to +100% (matches Journeyman/epic ground) so it just feels
--      like a normal epic mount with custom flair instead of a cheat
--      device.
--   2. No combat restriction. The spell currently has Attributes = 0 so
--      the engine lets the player cast it mid-fight. Every stock mount
--      spell has SPELL_ATTR0_NOT_IN_COMBAT_ONLY_PEACEFUL (0x00040000)
--      set; copying the full canonical mount-attribute set used by the
--      Goblin Trike (spell 87090) gives us the same gating without
--      reinventing it.
--   3. Cast is not interrupted by movement. With InterruptFlags = 0 the
--      1.5s cast bar completes even if the player keeps walking. Setting
--      InterruptFlags = 31 (MOVEMENT|PUSHBACK|INTERRUPT|AUTOATTACK|DAMAGE)
--      matches every other mount and forces the player to stop moving.
--   4. While at it, AuraInterruptFlags = 128 so the mount drops on the
--      same triggers retail mounts use (e.g. entering combat, dismount
--      action) instead of clinging through them.
--
-- The 2026_05_24_00 polish file's REPLACE INTO never specified Attributes
-- or the interrupt-flag columns, so they fell to the table default of 0;
-- that's why this needs a fresh UPDATE pass rather than just bumping the
-- BasePoints value.
-- ============================================================================

SET @BLACK_ROSE_MAULER_MOUNT := 900903;

UPDATE `spell_dbc`
   SET `EffectBasePoints_2`   = 99,         -- engine adds 1 -> +100% mount speed
       `Attributes`           = 269844752,  -- copies Goblin Trike (87090): includes
                                            -- SPELL_ATTR0_NOT_IN_COMBAT_ONLY_PEACEFUL,
                                            -- OUTDOORS_ONLY, HEARTBEAT_RESIST_CHECK, etc.
       `AttributesEx3`        = 536870912,  -- same row, SPELL_ATTR3 mount cluster
       `InterruptFlags`       = 31,         -- cast cancels on MOVEMENT | DAMAGE | etc.
       `AuraInterruptFlags`   = 128         -- mount drops on combat-enter / dismount
 WHERE `ID` = @BLACK_ROSE_MAULER_MOUNT;
