-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Dec 29, 2023 at 01:24 AM
-- Server version: 10.4.28-MariaDB
-- PHP Version: 8.1.17

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `mechanicorganizationalsystem`
--

-- --------------------------------------------------------

--
-- Table structure for table `dailymechanicworkhours`
--

CREATE TABLE `dailymechanicworkhours` (
  `MechanicID` int(11) NOT NULL,
  `Date` date NOT NULL,
  `TotalHours` time DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `dailymechanicworkhours`
--

INSERT INTO `dailymechanicworkhours` (`MechanicID`, `Date`, `TotalHours`) VALUES
(1, '2023-12-26', '01:08:29'),
(2, '2023-12-26', '00:00:22'),
(3, '2023-12-26', '03:41:25'),
(3, '2023-12-27', '00:00:05'),
(4, '2023-12-26', '01:00:19'),
(5, '2023-12-26', '01:07:53'),
(5, '2023-12-28', '00:00:00');

-- --------------------------------------------------------

--
-- Table structure for table `mechanics`
--

CREATE TABLE `mechanics` (
  `MechanicID` int(11) NOT NULL,
  `Name` varchar(255) NOT NULL,
  `ContactInfo` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `mechanics`
--

INSERT INTO `mechanics` (`MechanicID`, `Name`, `ContactInfo`) VALUES
(1, 'John Doe', 'johndoe@example.com'),
(2, 'carlos', 'carlos23@gmail.com'),
(3, 'Jane Smith', 'janesmith@example.com'),
(4, 'Alex Johnson', 'alexjohnson@example.com'),
(5, 'Maria Garcia', 'mariagarcia@example.com');

-- --------------------------------------------------------

--
-- Table structure for table `mechanicworkorder`
--

CREATE TABLE `mechanicworkorder` (
  `MechanicID` int(11) NOT NULL,
  `OrderID` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `mechanicworkorder`
--

INSERT INTO `mechanicworkorder` (`MechanicID`, `OrderID`) VALUES
(1, 10),
(1, 17),
(2, 15),
(2, 23),
(3, 10),
(4, 10),
(4, 21),
(5, 10),
(5, 35);

-- --------------------------------------------------------

--
-- Table structure for table `monthlymechanicworkhours`
--

CREATE TABLE `monthlymechanicworkhours` (
  `MechanicID` int(11) NOT NULL,
  `Month` varchar(50) NOT NULL,
  `TotalHours` time DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `monthlymechanicworkhours`
--

INSERT INTO `monthlymechanicworkhours` (`MechanicID`, `Month`, `TotalHours`) VALUES
(1, '2023-12', '02:37:29'),
(2, '2023-12', '22:28:00'),
(3, '2023-12', '04:30:16'),
(4, '2023-12', '01:02:46'),
(5, '2023-12', '01:11:51');

-- --------------------------------------------------------

--
-- Table structure for table `supplies`
--

CREATE TABLE `supplies` (
  `SupplyID` int(11) NOT NULL,
  `Name` varchar(255) NOT NULL,
  `Description` text NOT NULL,
  `QuantityInStock` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `supplies`
--

INSERT INTO `supplies` (`SupplyID`, `Name`, `Description`, `QuantityInStock`) VALUES
(1, 'Oil Filter', 'High-quality oil filter for various vehicle models', 50),
(2, 'Brake Pads', 'Durable brake pads suitable for most sedans', 40),
(3, 'Spark Plugs', 'High-performance spark plugs, set of 4', 100),
(4, 'Air Filter', 'Efficient air filter compatible with multiple car models', 30),
(5, 'Engine Oil', 'Synthetic motor oil, 5W-30, 1-liter bottles', 60),
(6, 'Timing Belt', 'Reinforced rubber timing belt for small to mid-sized engines', 20),
(7, 'Alternator', '12V alternator for light trucks and SUVs', 10),
(8, 'Windshield Wipers', 'Universal fit windshield wipers, 24-inch', 70),
(9, 'Battery', '12V car battery, suitable for a wide range of vehicles', 15),
(10, 'Radiator Coolant', 'Pre-mixed radiator coolant, 1-gallon bottles', 25),
(11, 'Tire Repair Kit', 'Complete tire repair kit with patches, adhesive, and tools', 30),
(12, 'Transmission Fluid', 'Automatic transmission fluid, 1-quart bottles', 40);

-- --------------------------------------------------------

--
-- Table structure for table `supplywaittimes`
--

CREATE TABLE `supplywaittimes` (
  `WaitID` int(11) NOT NULL,
  `OrderID` int(11) NOT NULL,
  `StartTime` datetime NOT NULL,
  `EndTime` datetime DEFAULT NULL,
  `VehicleName` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `supplywaittimes`
--

INSERT INTO `supplywaittimes` (`WaitID`, `OrderID`, `StartTime`, `EndTime`, `VehicleName`) VALUES
(1, 27, '2023-12-26 23:57:27', '2023-12-27 00:05:14', NULL),
(2, 27, '2023-12-27 00:05:25', '2023-12-27 00:05:26', NULL),
(3, 35, '2023-12-28 18:13:25', NULL, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `timetracking`
--

CREATE TABLE `timetracking` (
  `TrackingID` int(11) NOT NULL,
  `MechanicID` int(11) NOT NULL,
  `OrderID` int(11) NOT NULL,
  `StartTime` datetime NOT NULL,
  `EndTime` datetime DEFAULT NULL,
  `VehicleID` int(11) DEFAULT NULL,
  `Duration` varchar(20) GENERATED ALWAYS AS (concat(lpad(timestampdiff(HOUR,`StartTime`,`EndTime`),2,'0'),':',lpad(timestampdiff(MINUTE,`StartTime`,`EndTime`) MOD 60,2,'0'),':',lpad(timestampdiff(SECOND,`StartTime`,`EndTime`) MOD 60,2,'0'))) STORED
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `timetracking`
--

INSERT INTO `timetracking` (`TrackingID`, `MechanicID`, `OrderID`, `StartTime`, `EndTime`, `VehicleID`) VALUES
(2, 1, 3, '2023-12-19 11:41:02', '2023-12-19 12:18:20', 3),
(3, 3, 3, '2023-12-19 11:41:08', '2023-12-19 12:28:22', 3),
(4, 2, 3, '2023-12-19 12:00:17', '2023-12-19 12:28:19', 3),
(9, 1, 8, '2023-12-19 19:21:07', '2023-12-19 19:21:52', 3),
(10, 2, 9, '2023-12-19 19:24:25', '2023-12-19 19:28:00', 1),
(15, 1, 10, '2023-12-19 19:56:49', '2023-12-19 19:57:11', 2),
(16, 1, 10, '2023-12-19 19:57:53', '2023-12-19 19:59:21', 2),
(17, 3, 10, '2023-12-19 19:57:55', '2023-12-19 19:59:21', 2),
(18, 4, 10, '2023-12-19 19:58:00', '2023-12-19 19:59:21', 2),
(19, 5, 10, '2023-12-19 19:58:03', '2023-12-19 19:59:21', 2),
(20, 1, 11, '2023-12-20 09:10:45', '2023-12-20 09:10:49', 4),
(21, 1, 11, '2023-12-20 09:20:15', '2023-12-20 09:20:18', 4),
(22, 1, 11, '2023-12-20 09:20:23', '2023-12-20 10:07:39', 4),
(23, 2, 11, '2023-12-20 09:20:25', '2023-12-20 10:07:50', 4),
(24, 4, 12, '2023-12-20 10:10:24', '2023-12-20 10:11:08', 2),
(25, 5, 13, '2023-12-20 10:10:27', '2023-12-20 10:13:07', 1),
(26, 1, 14, '2023-12-20 10:13:20', '2023-12-20 10:13:25', 4),
(27, 3, 14, '2023-12-20 10:13:23', '2023-12-20 10:13:24', 4),
(28, 1, 15, '2023-12-20 10:35:58', '2023-12-20 10:36:36', 3),
(29, 2, 15, '2023-12-20 10:36:01', '2023-12-20 10:36:47', 3),
(30, 2, 16, '2023-12-20 10:49:09', '2023-12-20 11:16:10', 2),
(31, 1, 17, '2023-12-20 16:21:53', '2023-12-20 16:22:54', 2),
(32, 2, 18, '2023-12-20 16:25:33', '2023-12-21 13:00:06', 4),
(33, 2, 18, '2023-12-21 15:29:56', '2023-12-21 15:36:02', 4),
(34, 3, 18, '2023-12-21 15:36:10', '2023-12-21 15:36:15', 4),
(35, 4, 21, '2023-12-21 16:13:05', '2023-12-21 16:13:27', 4),
(36, 2, 23, '2023-12-21 16:32:16', '2023-12-21 16:32:18', 4),
(37, 2, 25, '2023-12-22 11:04:49', '2023-12-22 11:04:57', 4),
(38, 3, 25, '2023-12-26 14:12:29', '2023-12-26 14:12:50', 4),
(39, 5, 27, '2023-12-26 14:14:50', '2023-12-26 14:15:04', 3),
(40, 4, 28, '2023-12-26 14:14:53', '2023-12-26 14:15:12', 2),
(41, 1, 28, '2023-12-26 14:15:01', '2023-12-26 14:15:11', 2),
(42, 3, 25, '2023-12-26 14:22:11', '2023-12-26 14:26:14', 4),
(43, 1, 27, '2023-12-26 14:22:14', '2023-12-26 14:29:42', 3),
(44, 5, 28, '2023-12-26 14:22:17', '2023-12-26 15:28:07', 2),
(45, 2, 25, '2023-12-26 14:26:17', '2023-12-26 14:26:25', 4),
(46, 2, 25, '2023-12-26 14:29:38', '2023-12-26 14:29:46', 4),
(47, 4, 25, '2023-12-26 14:30:05', '2023-12-26 15:28:09', 4),
(48, 1, 27, '2023-12-26 14:30:09', '2023-12-26 15:28:08', 3),
(49, 5, 25, '2023-12-26 15:33:07', '2023-12-26 15:33:22', 4),
(50, 3, 25, '2023-12-26 15:50:46', '2023-12-26 15:51:28', 4),
(51, 3, 27, '2023-12-26 15:57:15', '2023-12-26 15:57:24', 3),
(52, 3, 27, '2023-12-26 16:04:36', '2023-12-26 16:05:29', 3),
(53, 1, 27, '2023-12-26 16:05:38', '2023-12-26 16:08:03', 3),
(54, 3, 28, '2023-12-26 16:05:41', '2023-12-26 16:07:45', 2),
(55, 4, 28, '2023-12-26 16:05:44', '2023-12-26 16:07:40', 2),
(56, 5, 28, '2023-12-26 16:05:47', '2023-12-26 16:07:21', 2),
(57, 2, 28, '2023-12-26 16:07:51', '2023-12-26 16:07:57', 2),
(58, 1, 27, '2023-12-26 16:30:12', '2023-12-26 16:30:32', 3),
(59, 1, 27, '2023-12-26 16:31:14', '2023-12-26 16:31:21', 3),
(60, 3, 27, '2023-12-26 17:17:36', '2023-12-26 20:50:49', 3),
(61, 3, 27, '2023-12-27 00:44:45', '2023-12-27 00:44:48', 3),
(62, 3, 27, '2023-12-27 19:30:25', '2023-12-27 19:30:27', 3),
(63, 5, 35, '2023-12-28 18:13:20', '2023-12-28 18:13:47', 4);

-- --------------------------------------------------------

--
-- Table structure for table `vehicles`
--

CREATE TABLE `vehicles` (
  `VehicleID` int(11) NOT NULL,
  `Type` varchar(255) NOT NULL,
  `VehicleName` varchar(255) DEFAULT NULL,
  `Status` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `vehicles`
--

INSERT INTO `vehicles` (`VehicleID`, `Type`, `VehicleName`, `Status`) VALUES
(1, 'Sedan', 'sed-55', 'Available'),
(2, 'Truck', 'cam-55', 'Available'),
(3, 'SUV', 'suv-33', 'Available'),
(4, 'Montacarga', 'MT-21', 'Available');

-- --------------------------------------------------------

--
-- Table structure for table `weeklymechanicworkhours`
--

CREATE TABLE `weeklymechanicworkhours` (
  `MechanicID` int(11) NOT NULL,
  `WeekStartDate` date NOT NULL,
  `TotalHours` time DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `weeklymechanicworkhours`
--

INSERT INTO `weeklymechanicworkhours` (`MechanicID`, `WeekStartDate`, `TotalHours`) VALUES
(1, '2023-12-25', '01:08:29'),
(2, '2023-12-25', '00:00:22'),
(3, '2023-12-25', '03:41:30'),
(4, '2023-12-25', '01:00:19'),
(5, '2023-12-25', '01:07:53');

-- --------------------------------------------------------

--
-- Table structure for table `workorders`
--

CREATE TABLE `workorders` (
  `OrderID` int(11) NOT NULL,
  `VehicleID` int(11) NOT NULL,
  `VehicleName` varchar(255) DEFAULT NULL,
  `Description` text DEFAULT NULL,
  `Status` varchar(100) NOT NULL,
  `WorkType` varchar(255) DEFAULT NULL,
  `CreatedTime` datetime DEFAULT current_timestamp(),
  `FinishedTime` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `workorders`
--

INSERT INTO `workorders` (`OrderID`, `VehicleID`, `VehicleName`, `Description`, `Status`, `WorkType`, `CreatedTime`, `FinishedTime`) VALUES
(3, 3, NULL, 'trabado por atras', 'Completed', NULL, '2023-12-20 11:28:15', NULL),
(8, 3, NULL, 'fucked up', 'Completed', NULL, '2023-12-20 11:28:15', NULL),
(9, 1, NULL, 'aaaa', 'Completed', 'Maintenance', '2023-12-20 11:28:15', NULL),
(10, 2, NULL, 'flask', 'Completed', 'Repair', '2023-12-20 11:28:15', NULL),
(11, 4, NULL, 'mamado a la verga', 'Completed', 'Repair', '2023-12-20 11:28:15', NULL),
(12, 2, NULL, 'se cagoi', 'Completed', 'Maintenance', '2023-12-20 11:28:15', NULL),
(13, 1, NULL, 'mamado', 'Completed', 'Maintenance', '2023-12-20 11:28:15', NULL),
(14, 4, NULL, 'cagado', 'Completed', 'Repair', '2023-12-20 11:28:15', NULL),
(15, 3, NULL, 'se chingo', 'Completed', 'Repair', '2023-12-20 11:28:15', NULL),
(16, 2, NULL, 'cagado', 'Completed', 'Repair', '2023-12-20 11:28:15', NULL),
(17, 2, NULL, 'penenegro', 'Completed', 'Repair', '2023-12-20 16:21:43', NULL),
(18, 4, NULL, 'carepa', 'Completed', 'Repair', '2023-12-20 16:23:06', NULL),
(19, 3, NULL, 'pp', 'Completed', 'Repair', '2023-12-21 13:00:01', NULL),
(20, 3, NULL, 'carlllll', 'Completed', 'Maintenance', '2023-12-21 15:44:32', '2023-12-21 15:44:37'),
(21, 4, NULL, 'pn', 'Completed', 'Repair', '2023-12-21 15:45:01', '2023-12-21 16:13:27'),
(22, 3, NULL, 'alakakka', 'Completed', 'Maintenance', '2023-12-21 16:14:02', '2023-12-21 16:14:16'),
(23, 4, NULL, 'rr', 'Completed', 'Repair', '2023-12-21 16:24:23', '2023-12-21 16:32:18'),
(24, 2, NULL, 'desc', 'Completed', 'Repair', '2023-12-21 16:32:45', '2023-12-21 16:32:54'),
(25, 4, NULL, 'ccccc', 'Completed', 'Maintenance', '2023-12-22 10:56:23', '2023-12-26 15:57:12'),
(26, 4, NULL, 'vvv', 'Completed', 'Repair', '2023-12-23 00:32:08', '2023-12-23 15:50:16'),
(27, 3, NULL, 'ggggg', 'Completed', 'Maintenance', '2023-12-23 00:46:43', '2023-12-28 17:42:25'),
(28, 2, NULL, 'vv', 'Completed', 'Repair', '2023-12-23 15:50:09', '2023-12-28 17:22:35'),
(29, 1, NULL, 's', 'Completed', 'Repair', '2023-12-26 23:52:50', '2023-12-28 17:42:16'),
(30, 4, NULL, 'vvv', 'Completed', 'Repair', '2023-12-27 15:09:43', '2023-12-28 17:40:26'),
(31, 2, NULL, 'ss', 'Completed', 'Repair', '2023-12-28 17:22:44', '2023-12-28 17:22:52'),
(32, 2, NULL, 'ss', 'Completed', 'Repair', '2023-12-28 17:22:59', '2023-12-28 17:27:24'),
(33, 2, NULL, 'xxx', 'Completed', 'Repair', '2023-12-28 17:27:30', '2023-12-28 17:40:15'),
(34, 2, NULL, 'ccc', 'Completed', 'Maintenance', '2023-12-28 17:42:36', '2023-12-28 17:42:41'),
(35, 4, NULL, 'ty6t', 'Completed', 'Maintenance', '2023-12-28 18:13:09', '2023-12-28 18:13:47');

-- --------------------------------------------------------

--
-- Table structure for table `workordersupplies`
--

CREATE TABLE `workordersupplies` (
  `OrderID` int(11) NOT NULL,
  `VehicleName` varchar(255) DEFAULT NULL,
  `SupplyID` int(11) NOT NULL,
  `Quantity` int(11) DEFAULT NULL,
  `Status` enum('Waiting','Ready','Received') DEFAULT 'Waiting',
  `ReceivedByMechanicID` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `workordersupplies`
--

INSERT INTO `workordersupplies` (`OrderID`, `VehicleName`, `SupplyID`, `Quantity`, `Status`, `ReceivedByMechanicID`) VALUES
(27, NULL, 2, 1, 'Received', 1),
(27, NULL, 4, 1, 'Received', 0),
(27, NULL, 5, 1, 'Waiting', NULL),
(27, NULL, 6, 1, 'Waiting', NULL),
(27, NULL, 10, 1, 'Waiting', NULL),
(35, NULL, 6, 1, 'Waiting', NULL);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `dailymechanicworkhours`
--
ALTER TABLE `dailymechanicworkhours`
  ADD PRIMARY KEY (`MechanicID`,`Date`);

--
-- Indexes for table `mechanics`
--
ALTER TABLE `mechanics`
  ADD PRIMARY KEY (`MechanicID`);

--
-- Indexes for table `mechanicworkorder`
--
ALTER TABLE `mechanicworkorder`
  ADD PRIMARY KEY (`MechanicID`,`OrderID`),
  ADD KEY `OrderID` (`OrderID`);

--
-- Indexes for table `monthlymechanicworkhours`
--
ALTER TABLE `monthlymechanicworkhours`
  ADD PRIMARY KEY (`MechanicID`,`Month`);

--
-- Indexes for table `supplies`
--
ALTER TABLE `supplies`
  ADD PRIMARY KEY (`SupplyID`);

--
-- Indexes for table `supplywaittimes`
--
ALTER TABLE `supplywaittimes`
  ADD PRIMARY KEY (`WaitID`),
  ADD KEY `OrderID` (`OrderID`),
  ADD KEY `FK_SupplyWaitTimes_Vehicles` (`VehicleName`);

--
-- Indexes for table `timetracking`
--
ALTER TABLE `timetracking`
  ADD PRIMARY KEY (`TrackingID`),
  ADD KEY `MechanicID` (`MechanicID`),
  ADD KEY `OrderID` (`OrderID`);

--
-- Indexes for table `vehicles`
--
ALTER TABLE `vehicles`
  ADD PRIMARY KEY (`VehicleID`),
  ADD UNIQUE KEY `UK_VehicleName` (`VehicleName`);

--
-- Indexes for table `weeklymechanicworkhours`
--
ALTER TABLE `weeklymechanicworkhours`
  ADD PRIMARY KEY (`MechanicID`,`WeekStartDate`);

--
-- Indexes for table `workorders`
--
ALTER TABLE `workorders`
  ADD PRIMARY KEY (`OrderID`),
  ADD KEY `VehicleID` (`VehicleID`),
  ADD KEY `FK_WorkOrders_Vehicles` (`VehicleName`);

--
-- Indexes for table `workordersupplies`
--
ALTER TABLE `workordersupplies`
  ADD PRIMARY KEY (`OrderID`,`SupplyID`),
  ADD KEY `SupplyID` (`SupplyID`),
  ADD KEY `FK_WorkOrderSupplies_Vehicles` (`VehicleName`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `mechanics`
--
ALTER TABLE `mechanics`
  MODIFY `MechanicID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `supplies`
--
ALTER TABLE `supplies`
  MODIFY `SupplyID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- AUTO_INCREMENT for table `supplywaittimes`
--
ALTER TABLE `supplywaittimes`
  MODIFY `WaitID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `timetracking`
--
ALTER TABLE `timetracking`
  MODIFY `TrackingID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=64;

--
-- AUTO_INCREMENT for table `vehicles`
--
ALTER TABLE `vehicles`
  MODIFY `VehicleID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `workorders`
--
ALTER TABLE `workorders`
  MODIFY `OrderID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=36;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `dailymechanicworkhours`
--
ALTER TABLE `dailymechanicworkhours`
  ADD CONSTRAINT `dailymechanicworkhours_ibfk_1` FOREIGN KEY (`MechanicID`) REFERENCES `mechanics` (`MechanicID`);

--
-- Constraints for table `mechanicworkorder`
--
ALTER TABLE `mechanicworkorder`
  ADD CONSTRAINT `MechanicWorkOrder_ibfk_1` FOREIGN KEY (`MechanicID`) REFERENCES `mechanics` (`MechanicID`),
  ADD CONSTRAINT `MechanicWorkOrder_ibfk_2` FOREIGN KEY (`OrderID`) REFERENCES `workorders` (`OrderID`);

--
-- Constraints for table `monthlymechanicworkhours`
--
ALTER TABLE `monthlymechanicworkhours`
  ADD CONSTRAINT `monthlymechanicworkhours_ibfk_1` FOREIGN KEY (`MechanicID`) REFERENCES `mechanics` (`MechanicID`);

--
-- Constraints for table `supplywaittimes`
--
ALTER TABLE `supplywaittimes`
  ADD CONSTRAINT `FK_SupplyWaitTimes_Vehicles` FOREIGN KEY (`VehicleName`) REFERENCES `vehicles` (`VehicleName`),
  ADD CONSTRAINT `supplywaittimes_ibfk_1` FOREIGN KEY (`OrderID`) REFERENCES `workorders` (`OrderID`);

--
-- Constraints for table `timetracking`
--
ALTER TABLE `timetracking`
  ADD CONSTRAINT `TimeTracking_ibfk_1` FOREIGN KEY (`MechanicID`) REFERENCES `mechanics` (`MechanicID`),
  ADD CONSTRAINT `TimeTracking_ibfk_2` FOREIGN KEY (`OrderID`) REFERENCES `workorders` (`OrderID`);

--
-- Constraints for table `weeklymechanicworkhours`
--
ALTER TABLE `weeklymechanicworkhours`
  ADD CONSTRAINT `weeklymechanicworkhours_ibfk_1` FOREIGN KEY (`MechanicID`) REFERENCES `mechanics` (`MechanicID`);

--
-- Constraints for table `workorders`
--
ALTER TABLE `workorders`
  ADD CONSTRAINT `FK_WorkOrders_Vehicles` FOREIGN KEY (`VehicleName`) REFERENCES `vehicles` (`VehicleName`),
  ADD CONSTRAINT `WorkOrders_ibfk_1` FOREIGN KEY (`VehicleID`) REFERENCES `vehicles` (`VehicleID`);

--
-- Constraints for table `workordersupplies`
--
ALTER TABLE `workordersupplies`
  ADD CONSTRAINT `FK_WorkOrderSupplies_Vehicles` FOREIGN KEY (`VehicleName`) REFERENCES `vehicles` (`VehicleName`),
  ADD CONSTRAINT `workordersupplies_ibfk_1` FOREIGN KEY (`OrderID`) REFERENCES `workorders` (`OrderID`),
  ADD CONSTRAINT `workordersupplies_ibfk_2` FOREIGN KEY (`SupplyID`) REFERENCES `supplies` (`SupplyID`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
