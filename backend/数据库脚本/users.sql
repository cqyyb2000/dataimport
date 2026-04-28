/*
 Navicat Premium Dump SQL

 Source Server         : 127.0.0.1
 Source Server Type    : MySQL
 Source Server Version : 80018 (8.0.18)
 Source Host           : localhost:3306
 Source Schema         : docdb_wfzx

 Target Server Type    : MySQL
 Target Server Version : 80018 (8.0.18)
 File Encoding         : 65001

 Date: 27/01/2026 14:24:37
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `password_hash` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `is_admin` tinyint(1) NULL DEFAULT 0,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `username`(`username` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 15 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of users
-- ----------------------------
INSERT INTO `users` VALUES (13, 'admin', 'scrypt:32768:8:1$QO4Rx7AkS46lXt3V$c4e3efe4cfb30220e033b4bef144df296a414549ba312b6979d4d1b8b2489721a7371b85d91c3621143bf01fdbecc76fd0607d48fa3d42b0a5eb30ea8bf2beb2', 1, '2025-02-18 16:26:05');
INSERT INTO `users` VALUES (14, 'usertest', 'scrypt:32768:8:1$2AwddzN1EZJZZJ74$a93550fd75f97ad317a3497744566b8a86348ce3ad3720744ec8ffb36f2a18d2b69fbc825bfa1b755fe06984f17860abb5ec7863015bc27260be339ce2216d0c', 0, '2025-11-07 15:11:25');

SET FOREIGN_KEY_CHECKS = 1;
