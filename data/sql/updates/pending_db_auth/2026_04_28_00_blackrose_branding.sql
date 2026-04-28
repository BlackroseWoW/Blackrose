-- Rename default realm and update login MOTD branding/rates text.
UPDATE `realmlist`
SET `name` = 'Theta'
WHERE `id` = 1;

REPLACE INTO `motd` (`realmid`, `text`) VALUES
(-1, 'Welcome to Blackrose - Theta realm. 3x XP rates. Hardcore mode available.');
