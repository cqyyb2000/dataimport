/*
 项目表 item（项目用 item 表示）
 与账套号、会计年度关联，公共档案按账套+年度维度存储
 依据 Share.json 中「项目」结构及 GB/T 24589.2-2010 设计

 Share.json 对应：
   项目编码 -> item_code
   项目名称 -> item_name
   级次 -> level
   项目类型 -> item_type
   项目类别 -> item_category
   项目属性 -> item_attribute
   项目起始日期 -> item_start_date
   项目结束日期 -> item_end_date

 关系：依赖 account_book_fiscal_year（账套+年度），同一账套同一年度下项目编码唯一

 Date: 2025-01
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- 项目表 item（按账套+年度）
-- ----------------------------
DROP TABLE IF EXISTS `item`;

CREATE TABLE `item` (
  `account_book_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账套编码，外键关联账套年度',
  `fiscal_year` int NOT NULL COMMENT '会计年度，4位如2021',
  `item_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '项目编码，对应 Share.json 项目编码',
  `item_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '项目名称，对应 Share.json 项目名称',
  `level` tinyint NOT NULL COMMENT '级次，对应 Share.json 级次，如 1、2',
  `item_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '项目类型，对应 Share.json 项目类型',
  `item_category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '项目类别，对应 Share.json 项目类别',
  `item_attribute` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '项目属性，对应 Share.json 项目属性',
  `item_start_date` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '项目起始日期，格式 YYYYMMDD，00000000 表示无',
  `item_end_date` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '项目结束日期，格式 YYYYMMDD，00000000 表示无',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '备注',
  `status` tinyint(1) DEFAULT 1 COMMENT '状态：1=启用 0=停用',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`account_book_code`, `fiscal_year`, `item_code`) USING BTREE,
  KEY `idx_fiscal_year` (`fiscal_year`) USING BTREE,
  KEY `idx_item_code` (`item_code`) USING BTREE,
  KEY `idx_item_name` (`item_name`(100)) USING BTREE,
  KEY `idx_level` (`level`) USING BTREE,
  KEY `idx_item_category` (`item_category`) USING BTREE,
  CONSTRAINT `fk_item_account_book_fiscal_year` FOREIGN KEY (`account_book_code`, `fiscal_year`) REFERENCES `account_book_fiscal_year` (`account_book_code`, `fiscal_year`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目表(item)，按账套+年度，对应 Share.json 项目';

SET FOREIGN_KEY_CHECKS = 1;
