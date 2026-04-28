/*
 币种表 currency
 与账套号、会计年度关联，公共档案按账套+年度维度存储
 依据 Share.json 中「币种」结构及 GB/T 24589.2-2010 设计

 Share.json 对应：
   币种编码 -> currency_code
   币种名称 -> currency_name

 关系：依赖 account_book_fiscal_year（账套+年度），同一账套同一年度下币种编码唯一

 Date: 2025-01
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- 币种表（按账套+年度）
-- ----------------------------
DROP TABLE IF EXISTS `currency`;

CREATE TABLE `currency` (
  `account_book_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账套编码，外键关联账套年度',
  `fiscal_year` int NOT NULL COMMENT '会计年度，4位如2021',
  `currency_code` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '币种编码，对应 Share.json 币种编码，如 RMB',
  `currency_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '币种名称，对应 Share.json 币种名称，如 人民币',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '备注',
  `status` tinyint(1) DEFAULT 1 COMMENT '状态：1=启用 0=停用',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`account_book_code`, `fiscal_year`, `currency_code`) USING BTREE,
  KEY `idx_fiscal_year` (`fiscal_year`) USING BTREE,
  KEY `idx_currency_code` (`currency_code`) USING BTREE,
  KEY `idx_currency_name` (`currency_name`) USING BTREE,
  CONSTRAINT `fk_currency_account_book_fiscal_year` FOREIGN KEY (`account_book_code`, `fiscal_year`) REFERENCES `account_book_fiscal_year` (`account_book_code`, `fiscal_year`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='币种表，按账套+年度，对应 Share.json 币种';

SET FOREIGN_KEY_CHECKS = 1;
