-- --------------------------------------------------------
-- Host:                         127.0.0.1
-- Server version:               10.4.17-MariaDB - mariadb.org binary distribution
-- Server OS:                    Win64
-- HeidiSQL Version:             11.3.0.6342
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- Dumping structure for table vmdb.tblBugTraq
DROP TABLE IF EXISTS `tblBugTraq`;
CREATE TABLE IF NOT EXISTS `tblBugTraq` (
  `iBugTraqID` int(11) DEFAULT NULL,
  `vcURL` varchar(250) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Dumping structure for table vmdb.tblCVEs
DROP TABLE IF EXISTS `tblCVEs`;
CREATE TABLE IF NOT EXISTS `tblCVEs` (
  `vcCVEID` varchar(15) DEFAULT NULL,
  `vcURL` varchar(250) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Dumping structure for table vmdb.tblLogs
DROP TABLE IF EXISTS `tblLogs`;
CREATE TABLE IF NOT EXISTS `tblLogs` (
  `dtTimestamp` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `vcScriptName` varchar(150) DEFAULT NULL,
  `vcLogEntry` varchar(15000) DEFAULT NULL,
  KEY `timestamp` (`dtTimestamp`) USING BTREE
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
  `vcCVEID` varchar(15) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Dumping structure for table vmdb.tblQID2Module
DROP TABLE IF EXISTS `tblQID2Module`;
CREATE TABLE IF NOT EXISTS `tblQID2Module` (
  `iQID` int(11) DEFAULT NULL,
  `iModID` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Dumping structure for table vmdb.tblScriptExecuteList
DROP TABLE IF EXISTS `tblScriptExecuteList`;
CREATE TABLE IF NOT EXISTS `tblScriptExecuteList` (
  `iExecuteID` int(11) NOT NULL AUTO_INCREMENT,
  `vcScriptName` varchar(150) NOT NULL,
  `dtStartTime` datetime NOT NULL,
  `dtStopTime` datetime DEFAULT NULL,
  `iGMTOffset` int(11) DEFAULT NULL,
  `bComplete` tinyint(4) DEFAULT 0,
  `iRowsUpdated` int(11) DEFAULT NULL,
  PRIMARY KEY (`iExecuteID`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4;

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
  `tSolution` text DEFAULT NULL,
  `iCVSSBase` int(11) NOT NULL,
  `iCVSSTemporal` int(11) NOT NULL,
  `bPCIFlag` tinyint(4) NOT NULL DEFAULT 0,
  `bRemoteDisc` tinyint(4) NOT NULL DEFAULT 0,
  `tAdditionalInfo` text DEFAULT NULL,
  `tConsequence` text DEFAULT NULL,
  `dtLastTouched` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
