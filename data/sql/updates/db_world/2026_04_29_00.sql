-- DB update 2026_04_27_00 -> 2026_04_29_00
-- Remove spirit healer spawns for hardcore setup.
DELETE c
FROM `creature` c
JOIN `creature_template` ct ON ct.`entry` = c.`id1`
WHERE (ct.`npcflag` & 16384) != 0;
