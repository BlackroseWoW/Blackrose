-- Clean up character inventory rows that reference the mod-worgoblin custom
-- starter items (49xxx / 525xx). Those item_template rows are removed by
-- modules/mod-worgoblin/data/sql/db-world/2026_05_26_04_worgoblin_remove_orphan_items.sql.
-- Without this cleanup the surviving item_instance / character_inventory rows
-- would dangle and turn into "Unknown Item" stubs on next login.
--
-- We collect the affected item_instance guids first, then delete both the
-- inventory mapping and the item_instance rows.

CREATE TEMPORARY TABLE IF NOT EXISTS `_worgoblin_orphan_item_guids` AS
SELECT `guid` FROM `item_instance` WHERE `itemEntry` IN (
    49399, 49400, 49401, 49403, 49404, 49406, 49407, 49408, 49409,
    49502, 49503, 49504, 49505, 49506, 49508, 49510, 49512,
    49514, 49515, 49516, 49520, 49521, 49522,
    49524, 49527, 49528, 49529, 49531,
    49563, 49564, 49565, 49566,
    49567, 49568, 49569, 49570, 49571,
    49572, 49573, 49574, 49575,
    49576, 49577, 49578, 49579,
    52532, 52550, 52551, 52552
);

DELETE FROM `character_inventory`
 WHERE `item` IN (SELECT `guid` FROM `_worgoblin_orphan_item_guids`);

DELETE FROM `mail_items`
 WHERE `item_guid` IN (SELECT `guid` FROM `_worgoblin_orphan_item_guids`);

DELETE FROM `auctionhouse`
 WHERE `itemguid` IN (SELECT `guid` FROM `_worgoblin_orphan_item_guids`);

DELETE FROM `item_instance`
 WHERE `guid` IN (SELECT `guid` FROM `_worgoblin_orphan_item_guids`);

DROP TEMPORARY TABLE `_worgoblin_orphan_item_guids`;
