-- ============================================================================
-- Black Rose | mod-worgoblin: racial mount vendors
--
-- Until the quest chain that hands out keys ships, these two NPCs are the
-- only way for a Goblin / Worgen to obtain their mount keys.
--
--   48510 Kall Worthaton    Trike Dealer    - Orgrimmar  (sells 62461, 62462)
--   48511 Lorna Crowley     Stable Master   - Stormwind  (sells 73838, 73839)
--
-- Riding skill itself is still taught by the existing vanilla trainers
-- (Randal Hunter / Ultham Ironhorn / Velma Warnam / Kar Stormsinger / etc.);
-- this module deliberately does NOT add a custom riding trainer.
--
-- Faction 35 (universally friendly) so faction-mixed Worgen / Goblin chars
-- in either capital can interact. Race-gating happens at the gossip layer
-- via CONDITION_RACE (type 16), matching what vanilla racial-only NPCs do
-- (see Skycaller Vrakthris 3161, etc.).
--
-- DELETEs are kept broad on purpose: the previous revision of this migration
-- also created riding-trainer NPCs (48512 Bullrok Bashstone, 48513 Revi
-- Ramrod) with their own gossip menus / texts / trainer templates.
-- Re-running this file wipes those rows so we don't leak orphan data into
-- the world.
-- ============================================================================

-- =====================================================================
-- 1. Drop any leftover trainer-template data from the prior revision
-- =====================================================================
DELETE FROM `trainer`        WHERE `Id` IN (1000, 1001);
DELETE FROM `trainer_spell`  WHERE `TrainerId` IN (1000, 1001);

-- =====================================================================
-- 2. Creature templates (the 2 vendor NPCs)
-- =====================================================================
-- npcflag 131 = GOSSIP|QUESTGIVER|VENDOR.
-- Display 7110 = "Citizen Female Human" - generic city-NPC look used by
-- the original supplementary SQL; safe stock display present in canon.
DELETE FROM `creature_template` WHERE `entry` IN (48510, 48511, 48512, 48513);
INSERT INTO `creature_template`
    (`entry`, `difficulty_entry_1`, `difficulty_entry_2`, `difficulty_entry_3`,
     `KillCredit1`, `KillCredit2`, `name`, `subname`, `IconName`,
     `gossip_menu_id`, `minlevel`, `maxlevel`, `exp`, `faction`, `npcflag`,
     `speed_walk`, `speed_run`, `speed_swim`, `speed_flight`, `detection_range`,
     `rank`, `dmgschool`, `DamageModifier`, `BaseAttackTime`, `RangeAttackTime`,
     `BaseVariance`, `RangeVariance`, `unit_class`, `unit_flags`, `unit_flags2`,
     `dynamicflags`, `family`, `type`, `type_flags`, `lootid`, `pickpocketloot`,
     `skinloot`, `PetSpellDataId`, `VehicleId`, `mingold`, `maxgold`, `AIName`,
     `MovementType`, `HoverHeight`, `HealthModifier`, `ManaModifier`,
     `ArmorModifier`, `ExperienceModifier`, `RacialLeader`, `movementId`,
     `RegenHealth`, `CreatureImmunitiesId`, `flags_extra`, `ScriptName`,
     `VerifiedBuild`)
VALUES
    (48510, 0, 0, 0, 0, 0, 'Kall Worthaton', 'Trike Dealer',   NULL, 25100,
     45, 45, 0, 35, 131, 1, 1.14286, 1, 1, 20, 0, 0, 1, 2000, 2000, 1, 1, 1,
     512, 2048, 0, 0, 7, 134217728, 0, 0, 0, 0, 0, 0, 0, '', 0, 1, 1, 1, 1, 1,
     0, 0, 1, 0, 2, '', 0),
    (48511, 0, 0, 0, 0, 0, 'Lorna Crowley', 'Stable Master',   NULL, 25102,
     45, 45, 0, 35, 131, 1, 1.14286, 1, 1, 20, 0, 0, 1, 2000, 2000, 1, 1, 1,
     512, 2048, 0, 0, 7, 134217728, 0, 0, 0, 0, 0, 0, 0, '', 0, 1, 1, 1, 1, 1,
     0, 0, 1, 0, 2, '', 0);

DELETE FROM `creature_template_model` WHERE `CreatureID` IN (48510, 48511, 48512, 48513);
INSERT INTO `creature_template_model`
    (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`, `VerifiedBuild`)
VALUES
    (48510, 0, 7110, 1, 1, 0),
    (48511, 0, 7110, 1, 1, 0);

-- =====================================================================
-- 3. Vendor stock
-- =====================================================================
DELETE FROM `npc_vendor` WHERE `entry` IN (48510, 48511);
INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`, `VerifiedBuild`)
VALUES
    (48510, 1, 62461, 0, 0, 0, 0),
    (48510, 2, 62462, 0, 0, 0, 0),
    (48511, 1, 73838, 0, 0, 0, 0),
    (48511, 2, 73839, 0, 0, 0, 0);

-- Trainer-NPC link from the prior revision - clean up
DELETE FROM `creature_default_trainer` WHERE `CreatureId` IN (48512, 48513);

-- =====================================================================
-- 4. Gossip menus, npc_text rows, and broadcast_text lines
-- =====================================================================
-- Vendor menus only - trainer menus (25101 / 25103) are dropped.
DELETE FROM `gossip_menu` WHERE `MenuID` IN (25100, 25101, 25102, 25103);
INSERT INTO `gossip_menu` (`MenuID`, `TextID`) VALUES
    (25100, 100100), (25100, 100110),
    (25102, 100102), (25102, 100112);

DELETE FROM `broadcast_text` WHERE `ID` BETWEEN 100100 AND 100113;
INSERT INTO `broadcast_text` (`ID`, `LanguageID`, `MaleText`, `FemaleText`, `EmoteID1`, `EmoteID2`, `EmoteID3`, `EmoteDelay1`, `EmoteDelay2`, `EmoteDelay3`, `SoundEntriesId`, `EmotesID`, `Flags`, `VerifiedBuild`) VALUES
    (100100, 0, 'Best trikes this side of Kezan, $c! What can I get you?',                   'Best trikes this side of Kezan, $c! What can I get you?',                   1, 0, 0, 0, 0, 0, 0, 0, 1, 0),
    (100110, 0, 'My wares are reserved for goblins. Move along, $c.',                        'My wares are reserved for goblins. Move along, $c.',                        1, 0, 0, 0, 0, 0, 0, 0, 1, 0),
    (100102, 0, 'Mountain horses are a Gilnean tradition, $c. Care to take one home?',       'Mountain horses are a Gilnean tradition, $c. Care to take one home?',       1, 0, 0, 0, 0, 0, 0, 0, 1, 0),
    (100112, 0, 'These mounts won\'t take to outsiders. Only worgen may ride them.',         'These mounts won\'t take to outsiders. Only worgen may ride them.',         1, 0, 0, 0, 0, 0, 0, 0, 1, 0);

DELETE FROM `npc_text` WHERE `ID` BETWEEN 100100 AND 100113;
INSERT INTO `npc_text` (`ID`, `text0_0`, `text0_1`, `BroadcastTextID0`, `lang0`, `Probability0`, `VerifiedBuild`) VALUES
    (100100, 'Best trikes this side of Kezan, $c! What can I get you?',             'Best trikes this side of Kezan, $c! What can I get you?',             100100, 0, 1, 0),
    (100110, 'My wares are reserved for goblins. Move along, $c.',                  'My wares are reserved for goblins. Move along, $c.',                  100110, 0, 1, 0),
    (100102, 'Mountain horses are a Gilnean tradition, $c. Care to take one home?', 'Mountain horses are a Gilnean tradition, $c. Care to take one home?', 100102, 0, 1, 0),
    (100112, 'These mounts won\'t take to outsiders. Only worgen may ride them.',   'These mounts won\'t take to outsiders. Only worgen may ride them.',   100112, 0, 1, 0);

-- OptionType 3 = GOSSIP_OPTION_VENDOR, OptionNpcFlag 128 = UNIT_NPC_FLAG_VENDOR.
DELETE FROM `gossip_menu_option` WHERE `MenuID` IN (25100, 25101, 25102, 25103);
INSERT INTO `gossip_menu_option`
    (`MenuID`, `OptionID`, `OptionIcon`, `OptionText`, `OptionBroadcastTextID`,
     `OptionType`, `OptionNpcFlag`, `ActionMenuID`, `ActionPoiID`,
     `BoxCoded`, `BoxMoney`, `BoxText`, `BoxBroadcastTextID`, `VerifiedBuild`)
VALUES
    (25100, 0, 1, 'I would like to browse your trikes.',   14967, 3, 128, 0, 0, 0, 0, NULL, 0, 0),
    (25102, 0, 1, 'Show me your mountain horses.',         14967, 3, 128, 0, 0, 0, 0, NULL, 0, 0);

-- =====================================================================
-- 5. Race-gating conditions
-- =====================================================================
-- Goblin = race 9 -> mask 256, Worgen = race 12 -> mask 2048.
-- SourceTypeOrReferenceId 14 = CONDITION_SOURCE_TYPE_GOSSIP_MENU_TEXT
--                        15 = CONDITION_SOURCE_TYPE_GOSSIP_MENU
-- ConditionTypeOrReference 16 = CONDITION_RACE.
DELETE FROM `conditions`
 WHERE `SourceTypeOrReferenceId` IN (14, 15)
   AND `SourceGroup` IN (25100, 25101, 25102, 25103);
INSERT INTO `conditions`
    (`SourceTypeOrReferenceId`, `SourceGroup`, `SourceEntry`, `SourceId`, `ElseGroup`,
     `ConditionTypeOrReference`, `ConditionTarget`, `ConditionValue1`, `ConditionValue2`,
     `ConditionValue3`, `NegativeCondition`, `ErrorType`, `ErrorTextId`, `ScriptName`,
     `Comment`)
VALUES
    (14, 25100, 100100, 0, 0, 16, 0, 256,  0, 0, 0, 0, 0, '', 'Kall Worthaton greeting - Goblin only'),
    (14, 25100, 100110, 0, 0, 16, 0, 256,  0, 0, 1, 0, 0, '', 'Kall Worthaton rejection - non-Goblin'),
    (15, 25100,      0, 0, 0, 16, 0, 256,  0, 0, 0, 0, 0, '', 'Kall Worthaton vendor option - Goblin only'),
    (14, 25102, 100102, 0, 0, 16, 0, 2048, 0, 0, 0, 0, 0, '', 'Lorna Crowley greeting - Worgen only'),
    (14, 25102, 100112, 0, 0, 16, 0, 2048, 0, 0, 1, 0, 0, '', 'Lorna Crowley rejection - non-Worgen'),
    (15, 25102,      0, 0, 0, 16, 0, 2048, 0, 0, 0, 0, 0, '', 'Lorna Crowley vendor option - Worgen only');

-- =====================================================================
-- 6. World spawns
-- =====================================================================
-- Coordinates were captured in-client via .gps at the pads the player picked:
--   Goblin pair: Orgrimmar (map 1, zone/area 1637 Orgrimmar).
--   Worgen pair: Stormwind City (map 0, zone/area 1519 Stormwind City).
-- GUIDs 5400001 / 5400003 used to hold the riding-trainer spawns; they get
--   wiped here and not re-inserted.
DELETE FROM `creature` WHERE `guid` IN (5400000, 5400001, 5400002, 5400003);
INSERT INTO `creature`
    (`guid`, `id1`, `id2`, `id3`, `map`, `zoneId`, `areaId`, `spawnMask`,
     `phaseMask`, `equipment_id`, `position_x`, `position_y`, `position_z`,
     `orientation`, `spawntimesecs`, `wander_distance`, `currentwaypoint`,
     `curhealth`, `curmana`, `MovementType`, `npcflag`, `unit_flags`,
     `dynamicflags`, `ScriptName`, `VerifiedBuild`)
VALUES
    -- Kall Worthaton  (Goblin Trike Dealer)   - Orgrimmar
    (5400000, 48510, 0, 0, 1, 1637, 1637, 1, 1, 0,  2042.684, -4753.928, 29.38759, 1.6516597, 300, 0, 0, 1, 0, 0, 0, 0, 0, '', 0),
    -- Lorna Crowley   (Worgen Mount Wrangler) - Stormwind
    (5400002, 48511, 0, 0, 0, 1519, 1519, 1, 1, 0, -8406.842,  683.43506, 95.28715, 4.9232183, 300, 0, 0, 1, 0, 0, 0, 0, 0, '', 0);
