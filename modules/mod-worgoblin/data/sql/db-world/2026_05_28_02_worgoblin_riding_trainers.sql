-- ============================================================================
-- Black Rose | mod-worgoblin: race-flavor Riding Trainers for Goblin + Worgen
--
-- The vanilla 3.3.5a riding trainers (Randal Hunter / Ogunaro Wolfrunner /
-- Kar Stormsinger / ...) are scattered across the classic starter zones, and
-- none of them is convenient to either of Black Rose's two custom races -
-- a fresh Goblin starting in Orgrimmar has to ride to Mulgore, and a fresh
-- Worgen starting in Stormwind has to ride to Dun Morogh, just to pay 4g for
-- Apprentice Riding. That's a terrible new-player loop.
--
-- This adds two dedicated riding trainers right next to the existing
-- mod-worgoblin mount vendors (Kall in Orgrimmar, Lorna in Stormwind), so
-- the "buy your mount + buy your skill" loop happens at one stop:
--
--   48512  Bullrok Bashstone   Riding Trainer  Orgrimmar  (Goblin male)
--   48513  Lana Crowmane       Riding Trainer  Stormwind  (Worgen female)
--
-- Both train the standard Apprentice (33388) + Journeyman (33391) riding
-- skills with the vanilla pricing/level gates - they're race-flavor, not
-- power-creep. Expert / Artisan / cold-weather flying come from the regular
-- TBC/WotLK trainers (those don't race-gate, so they work fine for
-- Worgen/Goblin out of the box).
--
-- An earlier prototype (48512 Bullrok Bashstone, 48513 Revi Ramrod) lived
-- in `supplementary/optional-mount-vendor.sql` and was deliberately removed
-- when the mount vendors were promoted to db-world/_01. This re-introduces
-- the riding trainers without re-introducing the redundant mount stalls.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. trainer instance definitions (Type=1 == TRAINER_TYPE_MOUNTS).
-- ---------------------------------------------------------------------------
DELETE FROM `trainer` WHERE `Id` IN (35001, 35002);
INSERT INTO `trainer` (`Id`, `Type`, `Requirement`, `Greeting`, `VerifiedBuild`) VALUES
(35001, 1, 0, 'Time is money, $c. Buy a riding skill, save a fortune in shoe leather.', 0),
(35002, 1, 0, 'The wild called to me. Let me share with you the skill to keep pace with it.', 0);

-- ---------------------------------------------------------------------------
-- 2. spells the two trainers offer - matches vanilla Apprentice/Journeyman.
-- This fork's `trainer_spell` schema (note: NO `ReqSpell` column, and
-- `ReqLevel` sits at the end before `VerifiedBuild`):
--   (TrainerId, SpellId, MoneyCost, ReqSkillLine, ReqSkillRank,
--    ReqAbility1, ReqAbility2, ReqAbility3, ReqLevel, VerifiedBuild)
-- These are the same MoneyCost / ReqSkillRank / ReqLevel values that
-- vanilla Randal Hunter (trainer Id=37) uses for the same two spells.
-- ---------------------------------------------------------------------------
DELETE FROM `trainer_spell` WHERE `TrainerId` IN (35001, 35002);
INSERT INTO `trainer_spell` (`TrainerId`, `SpellId`, `MoneyCost`, `ReqSkillLine`, `ReqSkillRank`, `ReqAbility1`, `ReqAbility2`, `ReqAbility3`, `ReqLevel`, `VerifiedBuild`) VALUES
-- Bullrok Bashstone (Orgrimmar)
(35001, 33388,  40000, 762,  0, 0, 0, 0, 20, 0),  -- Apprentice Riding   ( 4g, lvl 20)
(35001, 33391, 500000, 762, 75, 0, 0, 0, 40, 0),  -- Journeyman Riding   (50g, lvl 40)
-- Lana Crowmane (Stormwind)
(35002, 33388,  40000, 762,  0, 0, 0, 0, 20, 0),
(35002, 33391, 500000, 762, 75, 0, 0, 0, 40, 0);

-- ---------------------------------------------------------------------------
-- 3. creature_template entries. Re-use the 4851x reserved range so we don't
--    collide with anything else mod-worgoblin owns. Faction 35 is "Friendly,
--    All", so any race can technically train here - we don't gate via
--    `conditions` because riding is a universally useful skill and adding a
--    bunch of redundant convenience-trainer NPCs to Stormwind/Orgrimmar
--    would just clutter the cities.
-- ---------------------------------------------------------------------------
-- NOTE: this fork's `creature_template` has 55 effective columns. Compared
-- with the schema the supplementary file was written against:
--   * NO `trainer_type/_spell/_class/_race` (trainer linkage uses the
--     `creature_default_trainer` + `trainer` + `trainer_spell` triple)
--   * NO `scale`                          (dropped in 2026_03_22_03)
--   * NO `mechanic_immune_mask`, NO `spell_school_immune_mask` (dropped);
--     replaced by `CreatureImmunitiesId` FK into `creature_immunities`
DELETE FROM `creature_template` WHERE `entry` IN (48512, 48513);
INSERT INTO `creature_template` (`entry`, `difficulty_entry_1`, `difficulty_entry_2`, `difficulty_entry_3`, `KillCredit1`, `KillCredit2`,
    `name`, `subname`, `IconName`, `gossip_menu_id`,
    `minlevel`, `maxlevel`, `exp`, `faction`, `npcflag`,
    `speed_walk`, `speed_run`, `speed_swim`, `speed_flight`, `detection_range`,
    `rank`, `dmgschool`, `DamageModifier`, `BaseAttackTime`, `RangeAttackTime`,
    `BaseVariance`, `RangeVariance`, `unit_class`, `unit_flags`, `unit_flags2`,
    `dynamicflags`, `family`,
    `type`, `type_flags`, `lootid`, `pickpocketloot`, `skinloot`,
    `PetSpellDataId`, `VehicleId`, `mingold`, `maxgold`,
    `AIName`, `MovementType`, `HoverHeight`,
    `HealthModifier`, `ManaModifier`, `ArmorModifier`, `ExperienceModifier`,
    `RacialLeader`, `movementId`, `RegenHealth`,
    `CreatureImmunitiesId`, `flags_extra`,
    `ScriptName`, `VerifiedBuild`)
VALUES
    -- 48512 Bullrok Bashstone (Riding Trainer, Orgrimmar)
    (48512, 0, 0, 0, 0, 0,
     'Bullrok Bashstone', 'Riding Trainer', NULL, 0,
     50, 50, 0, 35, 16,
     1, 1.14286, 1, 1, 18,
     0, 0, 1, 2000, 2000,
     1, 1, 1, 512, 2048,
     0, 0,
     7, 0, 0, 0, 0,
     0, 0, 0, 0,
     '', 0, 1,
     1, 1, 1, 1,
     0, 0, 1,
     0, 2,
     '', 0),
    -- 48513 Lana Crowmane (Riding Trainer, Stormwind)
    (48513, 0, 0, 0, 0, 0,
     'Lana Crowmane', 'Riding Trainer', NULL, 0,
     50, 50, 0, 35, 16,
     1, 1.14286, 1, 1, 18,
     0, 0, 1, 2000, 2000,
     1, 1, 1, 512, 2048,
     0, 0,
     7, 0, 0, 0, 0,
     0, 0, 0, 0,
     '', 0, 1,
     1, 1, 1, 1,
     0, 0, 1,
     0, 2,
     '', 0);

-- ---------------------------------------------------------------------------
-- 4. creature_template_model - Goblin male / Worgen female playable displays
--    (29422/29423 from mod-worgoblin's ChrRaces overrides for race=12; the
--     Goblin DisplayID 6894 is one of the canonical NPC goblin-male models
--     and is consistent with what mod-worgoblin's race=9 player Goblin uses
--     for Kall Worthaton already once Lorna gets her hotfix below).
-- ---------------------------------------------------------------------------
DELETE FROM `creature_template_model` WHERE `CreatureID` IN (48512, 48513);
INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`, `VerifiedBuild`) VALUES
(48512, 0,  6894, 1, 1, 0),   -- Bullrok: Goblin male
(48513, 0, 29423, 1, 1, 0);   -- Lana   : Worgen female

-- ---------------------------------------------------------------------------
-- 5. Link creature -> trainer instance.
-- ---------------------------------------------------------------------------
DELETE FROM `creature_default_trainer` WHERE `CreatureId` IN (48512, 48513);
INSERT INTO `creature_default_trainer` (`CreatureId`, `TrainerId`) VALUES
(48512, 35001),
(48513, 35002);

-- ---------------------------------------------------------------------------
-- 6. World spawns.
--    Bullrok: Orgrimmar, immediately beside Kall Worthaton (the Goblin
--             mount vendor at 2042.684 / -4753.928).
--    Lana   : Stormwind, immediately beside Lorna Crowley (the Worgen
--             mount stable master at -8406.842 / 683.43506).
--    GUIDs 5400003 / 5400004 continue the 540000x range used by the
--    mount-vendor migration.
-- ---------------------------------------------------------------------------
DELETE FROM `creature` WHERE `id1` IN (48512, 48513);
INSERT INTO `creature` (`guid`, `id1`, `id2`, `id3`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `equipment_id`,
                        `position_x`, `position_y`, `position_z`, `orientation`, `spawntimesecs`,
                        `wander_distance`, `currentwaypoint`, `curhealth`, `curmana`,
                        `MovementType`, `npcflag`, `unit_flags`, `dynamicflags`, `ScriptName`, `VerifiedBuild`)
VALUES
    -- Bullrok Bashstone - Orgrimmar (next to Kall Worthaton)
    (5400003, 48512, 0, 0, 1, 1637, 1637, 1, 1, 0,  2045.20, -4756.10, 29.38759, 1.652, 300, 0, 0, 1, 0, 0, 0, 0, 0, '', 0),
    -- Lana Crowmane    - Stormwind (next to Lorna Crowley)
    (5400004, 48513, 0, 0, 0, 1519, 1519, 1, 1, 0, -8404.50,  681.00, 95.28715, 4.923, 300, 0, 0, 1, 0, 0, 0, 0, 0, '', 0);
