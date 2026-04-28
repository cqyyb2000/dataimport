/*
 自定义档案项表 custom_archive_item（自定义档案项定义）
 与账套号、会计年度关联，公共档案按账套+年度维度存储
 依据 Share.json 中「自定义档案项」结构及 GB/T 24589.2-2010 设计

 Share.json 对应：
   档案编码 -> archive_item_code
   档案名称 -> archive_item_name
   档案描述 -> archive_item_desc
   是否有层级特征 -> has_hierarchy
   档案编码规则 -> archive_code_rule

 关系：依赖 account_book_fiscal_year（账套+年度），同一账套同一年度下档案编码唯一

 Date: 2025-01
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- 自定义档案项表（按账套+年度）
-- ----------------------------
DROP TABLE IF EXISTS `custom_archive_item`;

CREATE TABLE `custom_archive_item` (
  `account_book_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账套编码，外键关联账套年度',
  `fiscal_year` int NOT NULL COMMENT '会计年度，4位如2021',
  `archive_item_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '档案编码，对应 Share.json 档案编码，如 ACC_ITEM1、B_ACC_CODE',
  `archive_item_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '档案名称，对应 Share.json 档案名称',
  `archive_item_desc` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '档案描述，对应 Share.json 档案描述',
  `has_hierarchy` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否有层级特征：1=是 0=否，对应 Share.json 是否有层级特征',
  `archive_code_rule` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '档案编码规则，对应 Share.json 档案编码规则，如 4-2-2-2、3-3-2',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '备注',
  `status` tinyint(1) DEFAULT 1 COMMENT '状态：1=启用 0=停用',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`account_book_code`, `fiscal_year`, `archive_item_code`) USING BTREE,
  KEY `idx_fiscal_year` (`fiscal_year`) USING BTREE,
  KEY `idx_archive_item_code` (`archive_item_code`) USING BTREE,
  KEY `idx_archive_item_name` (`archive_item_name`(100)) USING BTREE,
  KEY `idx_has_hierarchy` (`has_hierarchy`) USING BTREE,
  CONSTRAINT `fk_cai_account_book_fiscal_year` FOREIGN KEY (`account_book_code`, `fiscal_year`) REFERENCES `account_book_fiscal_year` (`account_book_code`, `fiscal_year`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='自定义档案项表(定义)，按账套+年度，对应 Share.json 自定义档案项';

SET FOREIGN_KEY_CHECKS = 1;
