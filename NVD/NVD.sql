CREATE TABLE `tblCPE` (
	`iCPEid` INT(11) NOT NULL AUTO_INCREMENT,
	`vcCVEid` VARCHAR(50) NOT NULL COLLATE 'latin1_swedish_ci',
	`vcVulnerable` VARCHAR(50) NULL DEFAULT NULL COLLATE 'latin1_swedish_ci',
	`vcCPEurl` VARCHAR(250) NULL DEFAULT NULL COLLATE 'latin1_swedish_ci',
	`vcVerStart` VARCHAR(20) NULL DEFAULT NULL COLLATE 'latin1_swedish_ci',
	`vcVerStop` VARCHAR(20) NULL DEFAULT NULL COLLATE 'latin1_swedish_ci',
	PRIMARY KEY (`iCPEid`) USING BTREE,
	INDEX `FK__tblNVD` (`vcCVEid`) USING BTREE,
	CONSTRAINT `FK__tblNVD` FOREIGN KEY (`vcCVEid`) REFERENCES `vmdb`.`tblNVD` (`vcCVEid`) ON UPDATE NO ACTION ON DELETE CASCADE
)
COMMENT='Table containing all the CPE records for a particular CVE from NVD, FK to tblNVD'
COLLATE='latin1_swedish_ci'
ENGINE=InnoDB
;
CREATE TABLE `tblNVD` (
	`vcCVEid` VARCHAR(50) NOT NULL DEFAULT 'Unknown' COLLATE 'latin1_swedish_ci',
	`vcCWEid` VARCHAR(50) NULL DEFAULT 'Unknown' COLLATE 'latin1_swedish_ci',
	`fImpactScore` FLOAT NULL DEFAULT NULL,
	`fExploitScore` FLOAT NULL DEFAULT NULL,
	`fCVSSv3` FLOAT NULL DEFAULT NULL,
	`vcVector` VARCHAR(150) NULL DEFAULT NULL COLLATE 'latin1_swedish_ci',
	`dtPubDate` DATETIME NULL DEFAULT NULL,
	`dtModDate` DATETIME NULL DEFAULT NULL,
	`strDescr` VARCHAR(9950) NULL DEFAULT NULL COLLATE 'latin1_swedish_ci',
	INDEX `vcCVEid` (`vcCVEid`) USING BTREE
)
COMMENT='Main table for the import of the National vuln database (NVD) from NIST'
COLLATE='latin1_swedish_ci'
ENGINE=InnoDB
;
