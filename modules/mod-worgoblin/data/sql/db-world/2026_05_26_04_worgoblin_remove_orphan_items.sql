-- mod-worgoblin: drop the race-flavoured starting-gear item_template rows the
-- module shipped (Gilnean*, Goblin*, Primal*, Worn Wood Chopper). They have no
-- client patch -- the matching Item.dbc / ItemDisplayInfo.dbc entries aren't in
-- our MPQs -- so they appeared as icon-less, name-only items. The starting
-- outfit table (charstartoutfit_dbc) now hands out vanilla items 1:1 from a
-- matching race, so these entries are unused.
--
-- Bag mounts and the language/skill data added by 2026_05_26_00_worgoblin_data.sql
-- are intentionally left in place.

DELETE FROM `item_template` WHERE `entry` IN (
    -- Worgen "Gilnean*" starter set
    49399, 49400, 49401, 49403, 49404, 49406, 49407, 49408, 49409,
    49563, 49564, 49565, 49566,
    49567, 49568, 49569, 49570, 49571,
    49572, 49573, 49574, 49575,
    49576, 49577, 49578, 49579,
    -- Goblin "Goblin*" / "Primal*" / Worn Wood Chopper starter set
    49502, 49503, 49504,
    49505, 49506, 49508,
    49510, 49512,
    49514, 49515, 49516,
    49520, 49521, 49522,
    49524, 49527, 49528, 49529,
    49531,
    52532,
    52550, 52551, 52552
);
