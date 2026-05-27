-- ============================================================================
-- Black Rose | mod-worgoblin: racial mounts - spellbook visibility
--
-- Mount keys + spells were already added by 2026_05_26_00_worgoblin_data.sql:
--   * Items 62461 (Goblin Trike Key), 62462 (Goblin Turbo-Trike Key),
--     73838 (Mountain Horse), 73839 (Swift Mountain Horse) teach the
--     matching spell via spelltrigger=6 (LEARN_SPELL).
--   * Spells 87090 / 87091 / 103195 / 103196 are in spell_dbc with
--     EffectAura 78 (MOUNTED) -> creature_template 46754 / 46755 / 55272 /
--     55273 -> creature_template_model -> display 35249 / 35250 / 39096 /
--     39095 -> Goblin Trike M2 (custom) and Horse model 65 with the
--     'HorseSkinBlack' / 'HorseSkinBrown' texture variations (stock).
--
-- What was missing: SkillLineAbility entries. Without them the spell is
-- learnable but invisible in the spellbook's Mounts tab, so the player has
-- no UI way to summon the mount after using the key (only /cast by name).
--
-- This migration adds the four SLA rows on skill 762 ('Riding'). Race-mask
-- is 256 (Goblin) for the trikes and 2048 (Worgen) for the horses, matching
-- the racial mount gating retail uses. MinSkillLineRank is 75 (Apprentice
-- Riding) for the basic mount and 150 (Expert Riding) for the swift version,
-- mirroring the item's RequiredSkillRank values.
--
-- AcquireMethod is 0 (manual learn) so the mount only appears in the
-- spellbook AFTER the character uses the key item; AcquireMethod=2 (auto
-- on skill-up) would hand every Goblin / Worgen the swift mount the
-- moment they trained Expert Riding, which we don't want.
--
-- Matching client-side rows live in tools/clientpatch/definitions/
-- skilllineability.json so a fresh patch rebuild ships the same IDs to the
-- client (server SLA gates skill-learning logic; client SLA drives the
-- spellbook UI).
-- ============================================================================

DELETE FROM `skilllineability_dbc` WHERE `ID` IN (22000, 22001, 22002, 22003);
INSERT INTO `skilllineability_dbc`
    (`ID`, `SkillLine`, `Spell`, `RaceMask`, `ClassMask`,
     `ExcludeRace`, `ExcludeClass`, `MinSkillLineRank`, `SupercededBySpell`,
     `AcquireMethod`, `TrivialSkillLineRankHigh`, `TrivialSkillLineRankLow`,
     `CharacterPoints_1`, `CharacterPoints_2`)
VALUES
    (22000, 762, 87090,  256,  0, 0, 0, 75,  0, 0, 0, 0, 0, 0),
    (22001, 762, 87091,  256,  0, 0, 0, 150, 0, 0, 0, 0, 0, 0),
    (22002, 762, 103195, 2048, 0, 0, 0, 75,  0, 0, 0, 0, 0, 0),
    (22003, 762, 103196, 2048, 0, 0, 0, 150, 0, 0, 0, 0, 0, 0);

-- skillline_dbc mirror for 762 ('Riding'). Already in canon 3.3.5a client
-- DBCs but the mod-worgoblin server mirror only imported skill rows the
-- module itself authored (789 Worgen Racial, 790 Goblin Racial). The
-- SkillLineAbility rows above join against this on AC's loader.
DELETE FROM `skillline_dbc` WHERE `ID` = 762;
INSERT INTO `skillline_dbc`
    (`ID`, `CategoryID`, `SkillCostsID`, `DisplayName_Lang_enUS`, `DisplayName_Lang_enGB`,
     `DisplayName_Lang_koKR`, `DisplayName_Lang_frFR`, `DisplayName_Lang_deDE`,
     `DisplayName_Lang_enCN`, `DisplayName_Lang_zhCN`, `DisplayName_Lang_enTW`,
     `DisplayName_Lang_zhTW`, `DisplayName_Lang_esES`, `DisplayName_Lang_esMX`,
     `DisplayName_Lang_ruRU`, `DisplayName_Lang_ptPT`, `DisplayName_Lang_ptBR`,
     `DisplayName_Lang_itIT`, `DisplayName_Lang_Unk`, `DisplayName_Lang_Mask`,
     `Description_Lang_enUS`, `Description_Lang_enGB`, `Description_Lang_koKR`,
     `Description_Lang_frFR`, `Description_Lang_deDE`, `Description_Lang_enCN`,
     `Description_Lang_zhCN`, `Description_Lang_enTW`, `Description_Lang_zhTW`,
     `Description_Lang_esES`, `Description_Lang_esMX`, `Description_Lang_ruRU`,
     `Description_Lang_ptPT`, `Description_Lang_ptBR`, `Description_Lang_itIT`,
     `Description_Lang_Unk`, `Description_Lang_Mask`, `SpellIconID`,
     `AlternateVerb_Lang_enUS`, `AlternateVerb_Lang_enGB`, `AlternateVerb_Lang_koKR`,
     `AlternateVerb_Lang_frFR`, `AlternateVerb_Lang_deDE`, `AlternateVerb_Lang_enCN`,
     `AlternateVerb_Lang_zhCN`, `AlternateVerb_Lang_enTW`, `AlternateVerb_Lang_zhTW`,
     `AlternateVerb_Lang_esES`, `AlternateVerb_Lang_esMX`, `AlternateVerb_Lang_ruRU`,
     `AlternateVerb_Lang_ptPT`, `AlternateVerb_Lang_ptBR`, `AlternateVerb_Lang_itIT`,
     `AlternateVerb_Lang_Unk`, `AlternateVerb_Lang_Mask`, `CanLink`)
VALUES
    (762, 9, 0, 'Riding', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 16712190,
                '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 16712172,
                414, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 16712172, 0);
