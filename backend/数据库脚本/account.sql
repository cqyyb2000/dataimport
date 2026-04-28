/*
 会计科目表 account（按账套+年度，对应 SHARE.xml 会计科目）
 科目辅助核算表 account_auxiliary（按账套+年度，对应 SHARE.xml 科目辅助核算）
 与账套号、会计年度关联，公共档案按账套+年度维度存储
 依据 SHARE.xml 中「会计科目」和「科目辅助核算」结构及 GB/T 24589.2-2010 设计

 SHARE.xml 对应：
   会计科目：
     科目编号 -> account_code
     科目名称 -> account_name
     科目级次 -> account_level
     科目类型 -> account_type
     余额方向 -> balance_direction
     是否末级 -> is_leaf
     是否启用 -> is_enabled
     上级科目编号 -> parent_account_code

   科目辅助核算：
     科目编号 -> account_code
     辅助项编号 -> auxiliary_item_code
     辅助项名称 -> auxiliary_item_name
     对应档案 -> corresponding_archive
     辅助项描述 -> auxiliary_item_description

 关系：依赖 account_book_fiscal_year（账套+年度），同一账套同一年度下科目编号唯一

 Date: 2026-02
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- 科目辅助核算表 account_auxiliary（从表，先删）
-- ----------------------------
DROP TABLE IF EXISTS `account_auxiliary`;
DROP TABLE IF EXISTS `account`;

-- ----------------------------
-- 会计科目表 account（按账套+年度）
-- ----------------------------
CREATE TABLE `account` (
  `account_book_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账套编码，外键关联账套年度',
  `fiscal_year` int NOT NULL COMMENT '会计年度，4位如2021',
  `account_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '科目编号，对应 SHARE.xml 科目编号',
  `account_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '科目名称，对应 SHARE.xml 科目名称',
  `account_level` tinyint NOT NULL COMMENT '科目级次，对应 SHARE.xml 科目级次，如 1、2',
  `account_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '科目类型，对应 SHARE.xml 科目类型：资产类/负债类/净资产类/收入类/支出类',
  `balance_direction` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '余额方向，对应 SHARE.xml 余额方向：借/贷',
  `is_leaf` tinyint(1) DEFAULT 0 COMMENT '是否末级，对应 SHARE.xml 是否末级：1=是 0=否',
  `is_enabled` tinyint(1) DEFAULT 1 COMMENT '是否启用，对应 SHARE.xml 是否启用：1=启用 0=停用',
  `parent_account_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '上级科目编号，对应 SHARE.xml 上级科目编号',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '备注',
  `status` tinyint(1) DEFAULT 1 COMMENT '状态：1=启用 0=停用',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`account_book_code`, `fiscal_year`, `account_code`) USING BTREE,
  KEY `idx_fiscal_year` (`fiscal_year`) USING BTREE,
  KEY `idx_account_code` (`account_code`) USING BTREE,
  KEY `idx_account_name` (`account_name`(100)) USING BTREE,
  KEY `idx_account_level` (`account_level`) USING BTREE,
  KEY `idx_account_type` (`account_type`) USING BTREE,
  KEY `idx_parent_account_code` (`parent_account_code`) USING BTREE,
  KEY `idx_account_book_fiscal_year` (`account_book_code`, `fiscal_year`) USING BTREE,
  CONSTRAINT `fk_account_account_book_fiscal_year` FOREIGN KEY (`account_book_code`, `fiscal_year`) REFERENCES `account_book_fiscal_year` (`account_book_code`, `fiscal_year`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_account_parent_account` FOREIGN KEY (`account_book_code`, `fiscal_year`, `parent_account_code`) REFERENCES `account` (`account_book_code`, `fiscal_year`, `account_code`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会计科目表(account)，按账套+年度，对应 SHARE.xml 会计科目';

-- ----------------------------
-- 科目辅助核算表 account_auxiliary（按账套+年度）
-- ----------------------------
CREATE TABLE `account_auxiliary` (
  `account_book_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账套编码，外键关联账套年度',
  `fiscal_year` int NOT NULL COMMENT '会计年度，4位如2021',
  `account_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '科目编号，外键关联 account，对应 SHARE.xml 科目编号',
  `auxiliary_item_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '辅助项编号，对应 SHARE.xml 辅助项编号',
  `auxiliary_item_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '辅助项名称，对应 SHARE.xml 辅助项名称',
  `corresponding_archive` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '对应档案，对应 SHARE.xml 对应档案',
  `auxiliary_item_description` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '辅助项描述，对应 SHARE.xml 辅助项描述',
  `status` tinyint(1) DEFAULT 1 COMMENT '状态：1=启用 0=停用',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`account_book_code`, `fiscal_year`, `account_code`, `auxiliary_item_code`) USING BTREE,
  KEY `idx_account_code` (`account_code`) USING BTREE,
  KEY `idx_auxiliary_item_code` (`auxiliary_item_code`) USING BTREE,
  KEY `idx_auxiliary_item_name` (`auxiliary_item_name`(100)) USING BTREE,
  KEY `idx_account_book_fiscal_year_account` (`account_book_code`, `fiscal_year`, `account_code`) USING BTREE,
  CONSTRAINT `fk_account_auxiliary_account_book_fiscal_year` FOREIGN KEY (`account_book_code`, `fiscal_year`) REFERENCES `account_book_fiscal_year` (`account_book_code`, `fiscal_year`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_account_auxiliary_account` FOREIGN KEY (`account_book_code`, `fiscal_year`, `account_code`) REFERENCES `account` (`account_book_code`, `fiscal_year`, `account_code`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='科目辅助核算表(account_auxiliary)，按账套+年度，对应 SHARE.xml 科目辅助核算';

SET FOREIGN_KEY_CHECKS = 1;
