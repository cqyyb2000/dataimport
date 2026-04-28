/*
 自定义档案值表 custom_archive_value（自定义档案数据）
 与账套号、会计年度关联，公共档案按账套+年度维度存储
 依据 Share.json 中「自定义档案值」结构及 GB/T 24589.2-2010 设计

 Share.json 对应：
   档案编码 -> archive_item_code（关联 custom_archive_item）
   档案值编码 -> archive_value_code
   档案值名称 -> archive_value_name
   档案值描述 -> archive_value_desc
   档案值父节点 -> parent_value_code
   档案值级次 -> level

 关系：依赖 custom_archive_item（档案项定义），同一档案项下档案值编码唯一，支持层级（父节点+级次）

 Date: 2025-01
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- 自定义档案值表（按账套+年度）
-- ----------------------------
DROP TABLE IF EXISTS `custom_archive_value`;

CREATE TABLE `custom_archive_value` (
  `account_book_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账套编码，外键关联账套年度',
  `fiscal_year` int NOT NULL COMMENT '会计年度，4位如2021',
  `archive_item_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '档案编码，对应 Share.json 档案编码，关联 custom_archive_item',
  `archive_value_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '档案值编码，对应 Share.json 档案值编码，如 0001、000101',
  `archive_value_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '档案值名称，对应 Share.json 档案值名称',
  `archive_value_desc` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '档案值描述，对应 Share.json 档案值描述',
  `parent_value_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '档案值父节点，对应 Share.json 档案值父节点，空表示根节点',
  `level` tinyint NOT NULL COMMENT '档案值级次，对应 Share.json 档案值级次，如 1、2',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '备注',
  `status` tinyint(1) DEFAULT 1 COMMENT '状态：1=启用 0=停用',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`account_book_code`, `fiscal_year`, `archive_item_code`, `archive_value_code`) USING BTREE,
  KEY `idx_fiscal_year` (`fiscal_year`) USING BTREE,
  KEY `idx_archive_item_code` (`archive_item_code`) USING BTREE,
  KEY `idx_archive_value_code` (`archive_value_code`) USING BTREE,
  KEY `idx_archive_value_name` (`archive_value_name`(100)) USING BTREE,
  KEY `idx_parent_value_code` (`parent_value_code`) USING BTREE,
  KEY `idx_level` (`level`) USING BTREE,
  CONSTRAINT `fk_cav_account_book_fiscal_year` FOREIGN KEY (`account_book_code`, `fiscal_year`) REFERENCES `account_book_fiscal_year` (`account_book_code`, `fiscal_year`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_cav_custom_archive_item` FOREIGN KEY (`account_book_code`, `fiscal_year`, `archive_item_code`) REFERENCES `custom_archive_item` (`account_book_code`, `fiscal_year`, `archive_item_code`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='自定义档案值表(数据)，按账套+年度，对应 Share.json 自定义档案值';

SET FOREIGN_KEY_CHECKS = 1;
