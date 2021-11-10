-- Dumping structure for table vmdb.tblBugTraq
DROP TABLE IF EXISTS `tblBugTraq`;
CREATE TABLE IF NOT EXISTS `tblBugTraq` (
  `iBugTraqID` int(11) DEFAULT NULL,
  `vcURL` varchar(250) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Dumping structure for table vmdb.tblCVEs
DROP TABLE IF EXISTS `tblCVEs`;
CREATE TABLE IF NOT EXISTS `tblCVEs` (
  `vcCVEID` varchar(35) DEFAULT NULL,
  `vcURL` varchar(250) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Dumping structure for table vmdb.tblModules
DROP TABLE IF EXISTS `tblModules`;
CREATE TABLE IF NOT EXISTS `tblModules` (
  `iModID` int(11) NOT NULL AUTO_INCREMENT,
  `vcModuleName` varchar(250) NOT NULL,
  PRIMARY KEY (`iModID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Dumping structure for table vmdb.tblQID2Bugtraq
DROP TABLE IF EXISTS `tblQID2Bugtraq`;
CREATE TABLE IF NOT EXISTS `tblQID2Bugtraq` (
  `iQID` int(11) DEFAULT NULL,
  `iBugTraqID` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Dumping structure for table vmdb.tblQID2CVE
DROP TABLE IF EXISTS `tblQID2CVE`;
CREATE TABLE IF NOT EXISTS `tblQID2CVE` (
  `iQID` int(11) DEFAULT NULL,
  `vcCVEID` varchar(35) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Dumping structure for table vmdb.tblQID2Module
DROP TABLE IF EXISTS `tblQID2Module`;
CREATE TABLE IF NOT EXISTS `tblQID2Module` (
  `iQID` int(11) DEFAULT NULL,
  `iModID` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Dumping structure for table vmdb.tblVulnDetails
DROP TABLE IF EXISTS `tblVulnDetails`;
CREATE TABLE IF NOT EXISTS `tblVulnDetails` (
  `iQID` int(11) NOT NULL,
  `iSeverity` int(11) DEFAULT NULL,
  `vcTitle` varchar(250) DEFAULT NULL,
  `vcCategory` varchar(250) DEFAULT NULL,
  `dtLastServiceModified` datetime DEFAULT NULL,
  `dtPublished` datetime DEFAULT NULL,
  `bPatchable` tinyint(4) NOT NULL DEFAULT 0,
  `tDiagnosis` text DEFAULT NULL,
  `tSolution` LONGTEXT DEFAULT NULL,
  `iCVSSBase` FLOAT NULL,
  `iCVSSTemporal` FLOAT NULL,
  `bPCIFlag` tinyint(4) NOT NULL DEFAULT 0,
  `bRemoteDisc` tinyint(4) NOT NULL DEFAULT 0,
  `tAdditionalInfo` LONGTEXT DEFAULT NULL,
  `tConsequence` LONGTEXT DEFAULT NULL,
  `dtLastTouched` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
