-- Dumping structure for table vmdb.tblLogs
DROP TABLE IF EXISTS `tblLogs`;
CREATE TABLE IF NOT EXISTS `tblLogs` (
  `dtTimestamp` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `vcScriptName` varchar(150) DEFAULT NULL,
  `vcLogEntry` varchar(15000) DEFAULT NULL,
  KEY `timestamp` (`dtTimestamp`) USING BTREE
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