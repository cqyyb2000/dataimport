/*
 汇率类型表 exchange_rate_type
 与账套号、会计年度关联，公共档案按账套+年度维度存储
 依据 Share.json 中「汇率类型」结构及 GB/T 24589.2-2010 设计

 Share.json 对应：
   汇率类型编号 -> exchange_rate_type_code
   汇率类型名称 -> exchange_rate_type_name

 关系：依赖 account_book_fiscal_year（账套+年度），同一账套同一年度下汇率类型编号唯一

 Date: 2025-01
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- 汇率类型表（按账套+年度）
-- ----------------------------
DROP TABLE IF EXISTS `exchange_rate_type`;

CREATE TABLE `exchange_rate_type` (
  `account_book_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账套编码，外键关联账套年度',
  `fiscal_year` int NOT NULL COMMENT '会计年度，4位如2021',
  `exchange_rate_type_code` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '汇率类型编号，对应 Share.json 汇率类型编号，如 01',
  `exchange_rate_type_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '汇率类型名称，对应 Share.json 汇率类型名称，如 固定汇率',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '备注',
  `status` tinyint(1) DEFAULT 1 COMMENT '状态：1=启用 0=停用',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`account_book_code`, `fiscal_year`, `exchange_rate_type_code`) USING BTREE,
  KEY `idx_fiscal_year` (`fiscal_year`) USING BTREE,
  KEY `idx_exchange_rate_type_code` (`exchange_rate_type_code`) USING BTREE,
  KEY `idx_exchange_rate_type_name` (`exchange_rate_type_name`) USING BTREE,
  CONSTRAINT `fk_ert_account_book_fiscal_year` FOREIGN KEY (`account_book_code`, `fiscal_year`) REFERENCES `account_book_fiscal_year` (`account_book_code`, `fiscal_year`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='汇率类型表，按账套+年度，对应 Share.json 汇率类型';

SET FOREIGN_KEY_CHECKS = 1;
