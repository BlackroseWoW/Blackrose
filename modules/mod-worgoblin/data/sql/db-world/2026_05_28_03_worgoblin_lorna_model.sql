-- ============================================================================
-- Black Rose | mod-worgoblin: Lorna Crowley display fix
--
-- The 2026_05_27_01 mount-vendor migration spawned Lorna with a placeholder
-- display ID of 7110, which is "Generic Human Female" - so the Worgen mount
-- stable master in Stormwind currently renders as a vanilla Human NPC and
-- breaks the "speak to your race's wrangler" fiction (it's particularly
-- jarring next to Kall, who already uses a flavor-correct Goblin model).
--
-- Swap her over to the same Worgen Female display the playable race uses
-- (29423, from mod-worgoblin's ChrRaces.dbc row for race 12). Same display
-- as the new Lana Crowmane riding trainer in _02, so they read as a matched
-- pair when you walk up to the stable.
-- ============================================================================

UPDATE `creature_template_model`
SET `CreatureDisplayID` = 29423
WHERE `CreatureID` = 48511 AND `Idx` = 0;
