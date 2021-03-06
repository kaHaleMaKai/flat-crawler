ATTACH DATABASE './flats.db' AS `flats`;

CREATE TABLE `flats`.`flat` ( `id` INTEGER,
	`title` TEXT,
	`address` TEXT,
	`street` TEXT,
	`zip` INTEGER,
	`district` TEXT,
	`city` TEXT,
	`area` REAL,
	`price` REAL,
	`rooms` REAL,
	`latitude` REAL,
	`longitude` REAL,
	`gmap_link` TEXT,
	`mail_pending` INTEGER default 0,
	`created_ts` datetime default (datetime('now', 'localtime')),
	`updated_ts` datetime default '0000-00-00 00:00:00',
	PRIMARY KEY (`id` ASC)
);
