CREATE DATABASE defiler;
GRANT ALL on defiler.* TO 'defiler'@'localhost';

USE defiler;

CREATE TABLE sessions (
    id char(20) NOT NULL PRIMARY KEY,
    created datetime,
    user_id int unsigned NULL,
    nickname char(64) NULL,
    INDEX created_idx(created),
    INDEX user_id_idx(user_id)
);

CREATE TABLE users (
    id serial,
    username char(32) unique,
    password char(128),
    nickname char(64) unique,
    pic char(256),
    gas int unsigned not null default 0,
    INDEX username_idx(username)
);

CREATE TABLE twitch (
    username char(64) PRIMARY KEY,
    token char(128),
    user_id int unsigned NULL UNIQUE,
    man_minutes_total int unsigned not null default 0,
    INDEX user_id_idx(user_id)
);

CREATE TABLE streams (
    slug char(128),
    creator int,
    name char(128),
    provider char(16),
    race ENUM("terran", "protoss", "zerg"),
    CONSTRAINT slug_provider UNIQUE (slug, provider),
    INDEX provider_idx (provider)
);

INSERT INTO users SET username='yoda', password=PASSWORD('123');

INSERT INTO streams SET slug='byflash', name='Flash', provider='afreeca', race='terran';
INSERT INTO streams SET slug='ioioiobb', name='By.Sun', provider='afreeca', race='protoss';
INSERT INTO streams SET slug='wodnrdldia', name='Best', provider='afreeca', race='protoss';

INSERT INTO `streams` VALUES ('byflash',NULL,'Flash','afreeca','terran',0);
INSERT INTO `streams` VALUES ('wodnrdldia',NULL,'Best','afreeca','protoss',0);
INSERT INTO `streams` VALUES ('first_smile',NULL,'first_smile','twitch',NULL,0);
INSERT INTO `streams` VALUES ('imeonzerg',NULL,'Eonzerg','twitch','zerg',0);
INSERT INTO `streams` VALUES ('must_die',NULL,'LancerX','twitch','protoss',0);
INSERT INTO `streams` VALUES ('kissname',NULL,'kissname','twitch',NULL,0);
INSERT INTO `streams` VALUES ('dyoda',NULL,'Yoda','twitch','zerg',0);
INSERT INTO `streams` VALUES ('drnelle',NULL,'drum','twitch','protoss',0);
INSERT INTO `streams` VALUES ('malkiyah',NULL,'Malki','twitch','zerg',0);
INSERT INTO `streams` VALUES ('aafnizzy',NULL,'nizzy','twitch',NULL,0);

