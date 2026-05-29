-- ============================================================================
-- Black Rose | mod-worgoblin: re-home Lorna + Lana onto vanilla NPC Worgen displays
--
-- Migration _03 set Lorna Crowley (48511) to DisplayID 29423 (mod-worgoblin's
-- playable Worgen Female wrapper, Model 3142) and _02 spawned Lana Crowmane
-- (48513) with the same display. Both displays ship with ExtendedDisplayInfoID
-- = 0, so the NPCs rendered as textureless blue silhouettes; an attempt to
-- bind a fresh CreatureDisplayInfoExtra row to 29423 instead CTD'd the client
-- as soon as the player entered render distance (the vanilla 3.3.5a NPC bake
-- pipeline has no working code path for `Race=Worgen, Gender=Female` - that
-- combination was first introduced in Cataclysm, and the engine null-derefs
-- on one of the customization-geoset lookups no matter what we put in the
-- Extra row).
--
-- Pivoting both NPCs onto vanilla NPC Worgen displays (Model 44 =
-- Creature\Worgen\Worgen.mdx) instead - the M2 file has baked textures, so
-- the displays don't need a CreatureDisplayInfoExtra at all and don't trip
-- the broken bake path. Visually they read as male Worgens, so the NPCs get
-- renamed to match.
--
--   48511 Lorna Crowley -> Lorne Crowley   DisplayID 524 (Brown,  scale 1.15)
--   48513 Lana Crowmane -> Lane Crowmane   DisplayID 729 (White,  scale 1.00)
--
-- Both NPCs keep their existing trainer/vendor wiring, faction, spawn point,
-- and gossip-menu race gate (still Worgen-only access via condition rows from
-- 2026_05_27_01). The mount vendor + riding trainer loop continues to work
-- exactly as before; only the visual model and first name change.
-- ============================================================================

-- 1. Rename in creature_template.
UPDATE `creature_template` SET `name` = 'Lorne Crowley' WHERE `entry` = 48511;
UPDATE `creature_template` SET `name` = 'Lane Crowmane' WHERE `entry` = 48513;

-- 2. Swap display IDs to vanilla NPC Worgen variants. DELETE + INSERT (instead
--    of UPDATE) so the row's DisplayScale / Probability / VerifiedBuild are
--    restored to clean defaults if any prior migration set them oddly.
DELETE FROM `creature_template_model` WHERE `CreatureID` IN (48511, 48513);
INSERT INTO `creature_template_model`
    (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`, `VerifiedBuild`)
VALUES
    (48511, 0, 524, 1, 1, 0),   -- Lorne Crowley:  vanilla NPC Worgen (Brown,  scale 1.15)
    (48513, 0, 729, 1, 1, 0);   -- Lane  Crowmane: vanilla NPC Worgen (White,  scale 1.00)
