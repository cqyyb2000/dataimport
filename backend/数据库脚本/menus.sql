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

 Date: 27/01/2026 14:25:07
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for menus
-- ----------------------------
DROP TABLE IF EXISTS `menus`;
CREATE TABLE `menus`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `component` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `parent_id` int(11) NULL DEFAULT 0,
  `path` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `icon` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `sort_order` int(11) NULL DEFAULT 0,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 20 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of menus
-- ----------------------------
INSERT INTO `menus` VALUES (11, '系统管理', '', 0, '', 'Setting', 0, '2025-02-18 15:49:01');
INSERT INTO `menus` VALUES (12, '用户管理', 'system/UserManage', 11, '/system/UserManage', 'User', 0, '2025-02-18 15:49:01');
INSERT INTO `menus` VALUES (13, '菜单管理', 'system/MenuManage', 11, '/system/MenuManage', 'Menu', 0, '2025-02-18 15:49:01');
INSERT INTO `menus` VALUES (14, '权限管理', 'system/PermissionManage', 11, '/system/PermissionManage', 'Lock', 0, '2025-02-18 15:49:01');
INSERT INTO `menus` VALUES (15, '档案管理', '', 0, '', 'Lock', 0, '2025-03-28 09:02:19');
INSERT INTO `menus` VALUES (16, '档案查询', 'doc/DocQuery', 15, '/doc/DocQuery', 'Lock', 0, '2025-03-28 09:06:03');
INSERT INTO `menus` VALUES (18, '档案上传', 'doc/DocUpload', 15, '/doc/DocUpload', 'Lock', 0, '2025-05-13 22:59:25');
INSERT INTO `menus` VALUES (19, '档案目录', 'system/DocCatalog', 11, '/system/DocCatalog', 'SetUp', 0, '2025-05-20 13:55:09');

SET FOREIGN_KEY_CHECKS = 1;
