USE `rte`;
SET foreign_key_checks = 0;

DROP TABLE IF EXISTS `settings`;
CREATE TABLE `settings` ( 
    `skey` VARCHAR(255) NOT NULL PRIMARY KEY,
    `value` VARCHAR(255) NOT NULL);

DROP TABLE IF EXISTS `teams`;
CREATE TABLE `teams` ( 
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(255) NOT NULL UNIQUE,
    `ip` VARCHAR(255) NOT NULL,
    `difficulty` INT NOT NULL);

DROP TABLE IF EXISTS `systems`;
CREATE TABLE `systems` (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `num` INT NOT NULL,
    `status`  VARCHAR(255) NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `team_id` INT NOT NULL,
    `ip` VARCHAR(255) NOT NULL,
    `os` VARCHAR(255) NOT NULL,
    `flavor` VARCHAR(255) NOT NULL);
    
DROP TABLE IF EXISTS `modules`;
CREATE TABLE `modules` (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(255) NOT NULL,
    `os` VARCHAR(255) NOT NULL,
    `flavor` VARCHAR(255) NOT NULL,
    `mod_type` VARCHAR(255) NOT NULL,
    `mod_lang` VARCHAR(255) NOT NULL,
    `destructive` VARCHAR(255) NOT NULL,
    `scannable` VARCHAR(255) NOT NULL,
    `difficulty` INT NOT NULL,
    `priv_required` VARCHAR(255) NOT NULL);
    
DROP TABLE IF EXISTS `vulns`;
CREATE TABLE `vulns` (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `system_id` INT NOT NULL,
    `mod_name` VARCHAR(255) NOT NULL,
    `mod_info` VARCHAR(4095) NOT NULL);

DROP TABLE IF EXISTS `access_log`;
CREATE TABLE `access_log` (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `cycle` INT NOT NULL,
	`team_id` INT NOT NULL,
	`shells` INT NOT NULL);
    
SET foreign_key_checks = 1;



