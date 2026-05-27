-- ============================================================================
-- Black Rose | mod-worgoblin: racial mount speed correction
--
-- The original spell_dbc rows for these mounts were copied straight from
-- retail Cataclysm, where the same spell was BOTH a ground mount AND a
-- flying mount (the "Mount Up - Use Best Available" pattern). That layout
-- looks like this:
--
--   Effect_1: APPLY_AURA / SPELL_AURA_MOUNTED (78)
--             EffectMiscValue_1 = creature template (visual)
--   Effect_2: APPLY_AURA / SPELL_AURA_MOD_FLIGHT_SPEED_MOUNTED (207)
--             EffectBasePoints_2 = 309  -> +310% flight speed
--   Effect_3: APPLY_AURA / SPELL_AURA_MOD_INCREASE_MOUNTED_SPEED (32)
--             EffectBasePoints_3 = 59 / 99  -> +60% / +100% ground speed
--
-- On WotLK (3.3.5a) these mounts can only ever ground-mount, so Effect_2's
-- flight-speed aura should be inert - but it isn't always. AC layers
-- aura 207 on top of aura 32, which in some movement paths results in the
-- mount moving at roughly flight-speed numbers even on dirt. That's what
-- the player observed when both the apprentice and journeyman trikes felt
-- equally absurdly fast.
--
-- Fix: clear Effect_2 entirely. Aura 32 (Effect_3) does all the work and
-- already carries the correct rank-appropriate value:
--
--   Apprentice  rank-75  mounts: Effect_3 BasePoints = 59  -> +60%
--   Journeyman  rank-150 mounts: Effect_3 BasePoints = 99  -> +100%
-- ============================================================================

UPDATE `spell_dbc`
   SET `Effect_2`             = 0,
       `EffectAura_2`         = 0,
       `EffectBasePoints_2`   = 0,
       `EffectMiscValue_2`    = 0,
       `EffectDieSides_2`     = 0,
       `ImplicitTargetA_2`    = 0
 WHERE `ID` IN (87090, 87091, 103195, 103196);
