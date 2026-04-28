/*
 总账类数据表（GL.xml）
 依据 GB/T 24589.2-2010 数据接口规范设计
 包含5个主要数据表：
 1. gl_base_info - 总账基础信息
 2. gl_voucher_type - 记账凭证类型
 3. gl_voucher - 记账凭证
 4. gl_voucher_entry - 记账凭证分录行
 5. gl_account_balance - 科目余额

 设计原则：
 - 所有表按账套+年度维度存储，关联 account_book_fiscal_year
 - 支持同一账套导入不同年度的总账数据
 - 凭证和分录行通过凭证编号+会计年度+会计期间号关联
 - 科目余额按科目+年度+期间存储

 Date: 2026-02
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- 1. 总账基础信息表 gl_base_info
-- ----------------------------
DROP TABLE IF EXISTS `gl_base_info`;

CREATE TABLE `gl_base_info` (
  `account_book_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账套编码，外键关联账套年度',
  `fiscal_year` int NOT NULL COMMENT '会计年度，4位如2021',
  `structure_separator` varchar(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '结构分隔符，科目编号的分隔符，对应 XML 结构分隔符',
  `account_code_rule` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '会计科目编号规则，对应 XML 会计科目编号规则',
  `voucher_header_ext_fields` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '凭证头可扩展字段结构，对应 XML 凭证头可扩展字段结构',
  `voucher_header_ext_archives` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '凭证头可扩展结构对应档案，对应 XML 凭证头可扩展结构对应档案',
  `entry_line_ext_fields` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '分录行可扩展字段结构，对应 XML 分录行可扩展字段结构',
  `entry_line_ext_archives` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '分录行可扩展字段对应档案，对应 XML 分录行可扩展字段对应档案',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`account_book_code`, `fiscal_year`) USING BTREE,
  CONSTRAINT `fk_gl_base_info_account_book_fiscal_year` FOREIGN KEY (`account_book_code`, `fiscal_year`) REFERENCES `account_book_fiscal_year` (`account_book_code`, `fiscal_year`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='总账基础信息表，对应 GL.xml 总账基础信息，按账套+年度';

-- ----------------------------
-- 2. 记账凭证类型表 gl_voucher_type
-- ----------------------------
DROP TABLE IF EXISTS `gl_voucher_type`;

CREATE TABLE `gl_voucher_type` (
  `account_book_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账套编码，外键关联账套年度',
  `fiscal_year` int NOT NULL COMMENT '会计年度，4位如2021',
  `voucher_type_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '记账凭证类型编号，对应 XML 记账凭证类型编号',
  `voucher_type_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '记账凭证类型名称，对应 XML 记账凭证类型名称',
  `voucher_type_abbreviation` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '记账凭证类型简称，对应 XML 记账凭证类型简称',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`account_book_code`, `fiscal_year`, `voucher_type_code`) USING BTREE,
  KEY `idx_voucher_type_code` (`voucher_type_code`) USING BTREE,
  KEY `idx_voucher_type_name` (`voucher_type_name`(100)) USING BTREE,
  CONSTRAINT `fk_gl_voucher_type_account_book_fiscal_year` FOREIGN KEY (`account_book_code`, `fiscal_year`) REFERENCES `account_book_fiscal_year` (`account_book_code`, `fiscal_year`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='记账凭证类型表，对应 GL.xml 记账凭证类型，按账套+年度';

-- ----------------------------
-- 3. 记账凭证表 gl_voucher
-- ----------------------------
DROP TABLE IF EXISTS `gl_voucher`;

CREATE TABLE `gl_voucher` (
  `account_book_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账套编码，外键关联账套年度',
  `fiscal_year` int NOT NULL COMMENT '会计年度，4位如2021，对应 XML 会计年度',
  `period_number` tinyint NOT NULL COMMENT '会计期间号，1-12或13，对应 XML 会计期间号',
  `voucher_number` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '凭证编号，对应 XML 凭证编号',
  `voucher_date` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '凭证日期，格式 YYYYMMDD，对应 XML 凭证日期',
  `voucher_type_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '记账凭证类型编号，外键关联 gl_voucher_type，对应 XML 记账凭证类型编号',
  `attachment_count` int DEFAULT NULL COMMENT '附单据数，对应 XML 附单据数',
  `prepared_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '制单人，对应 XML 制单人',
  `reviewed_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '审核人，对应 XML 审核人',
  `posted_by` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '记账人，对应 XML 记账人',
  `voucher_status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '凭证状态，对应 XML 凭证状态',
  `summary` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '凭证摘要，对应 XML 摘要',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`account_book_code`, `fiscal_year`, `period_number`, `voucher_number`) USING BTREE,
  KEY `idx_fiscal_year_period` (`fiscal_year`, `period_number`) USING BTREE,
  KEY `idx_voucher_number` (`voucher_number`) USING BTREE,
  KEY `idx_voucher_date` (`voucher_date`) USING BTREE,
  KEY `idx_voucher_type_code` (`voucher_type_code`) USING BTREE,
  KEY `idx_voucher_status` (`voucher_status`) USING BTREE,
  CONSTRAINT `fk_gl_voucher_account_book_fiscal_year` FOREIGN KEY (`account_book_code`, `fiscal_year`) REFERENCES `account_book_fiscal_year` (`account_book_code`, `fiscal_year`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_gl_voucher_voucher_type` FOREIGN KEY (`account_book_code`, `fiscal_year`, `voucher_type_code`) REFERENCES `gl_voucher_type` (`account_book_code`, `fiscal_year`, `voucher_type_code`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='记账凭证表，对应 GL.xml 记账凭证，按账套+年度+期间+凭证编号';

-- ----------------------------
-- 4. 记账凭证分录行表 gl_voucher_entry
-- ----------------------------
DROP TABLE IF EXISTS `gl_voucher_entry`;

CREATE TABLE `gl_voucher_entry` (
  `account_book_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账套编码，外键关联账套年度',
  `fiscal_year` int NOT NULL COMMENT '会计年度，4位如2021',
  `period_number` tinyint NOT NULL COMMENT '会计期间号，1-12或13',
  `voucher_number` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '凭证编号，外键关联 gl_voucher，对应 XML 凭证编号',
  `entry_line_number` int NOT NULL COMMENT '分录行号，对应 XML 分录行号',
  `account_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '科目编号，对应 XML 科目编号',
  `summary` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '分录摘要，对应 XML 摘要',
  `debit_amount` decimal(18,2) DEFAULT NULL COMMENT '借方金额，对应 XML 借方金额',
  `credit_amount` decimal(18,2) DEFAULT NULL COMMENT '贷方金额，对应 XML 贷方金额',
  `currency_code` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '币种编码，对应 XML 币种编码',
  `exchange_rate` decimal(18,6) DEFAULT NULL COMMENT '汇率，对应 XML 汇率',
  `original_currency_debit_amount` decimal(18,2) DEFAULT NULL COMMENT '原币借方金额，对应 XML 原币借方金额',
  `original_currency_credit_amount` decimal(18,2) DEFAULT NULL COMMENT '原币贷方金额，对应 XML 原币贷方金额',
  `quantity` decimal(18,4) DEFAULT NULL COMMENT '数量，对应 XML 数量',
  `unit_price` decimal(18,4) DEFAULT NULL COMMENT '单价，对应 XML 单价',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`account_book_code`, `fiscal_year`, `period_number`, `voucher_number`, `entry_line_number`) USING BTREE,
  KEY `idx_voucher_number` (`voucher_number`) USING BTREE,
  KEY `idx_account_code` (`account_code`) USING BTREE,
  KEY `idx_fiscal_year_period` (`fiscal_year`, `period_number`) USING BTREE,
  KEY `idx_currency_code` (`currency_code`) USING BTREE,
  CONSTRAINT `fk_gl_voucher_entry_account_book_fiscal_year` FOREIGN KEY (`account_book_code`, `fiscal_year`) REFERENCES `account_book_fiscal_year` (`account_book_code`, `fiscal_year`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_gl_voucher_entry_voucher` FOREIGN KEY (`account_book_code`, `fiscal_year`, `period_number`, `voucher_number`) REFERENCES `gl_voucher` (`account_book_code`, `fiscal_year`, `period_number`, `voucher_number`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='记账凭证分录行表，对应 GL.xml 记账凭证分录行，按账套+年度+期间+凭证编号+分录行号';

-- ----------------------------
-- 5. 科目余额表 gl_account_balance
-- ----------------------------
DROP TABLE IF EXISTS `gl_account_balance`;

CREATE TABLE `gl_account_balance` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `account_book_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账套编码，外键关联账套年度',
  `fiscal_year` int NOT NULL COMMENT '会计年度，4位如2021，对应 XML 会计年度',
  `period_number` tinyint NOT NULL COMMENT '会计期间号，0表示期初，1-12表示各期间，对应 XML 会计期间号',
  `account_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '科目编号，对应 XML 科目编号',
  `opening_balance` decimal(18,2) DEFAULT NULL COMMENT '期初余额，对应 XML 期初余额',
  `opening_balance_direction` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '期初余额方向，借/贷，对应 XML 期初余额方向',
  `current_period_debit_amount` decimal(18,2) DEFAULT NULL COMMENT '本期借方发生额，对应 XML 本期借方发生额',
  `current_period_credit_amount` decimal(18,2) DEFAULT NULL COMMENT '本期贷方发生额，对应 XML 本期贷方发生额',
  `closing_balance` decimal(18,2) DEFAULT NULL COMMENT '期末余额，对应 XML 期末余额',
  `closing_balance_direction` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '期末余额方向，借/贷，对应 XML 期末余额方向',
  `currency_code` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '币种编码，对应 XML 币种编码',
  `ParentCode` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '父级科目编号',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uk_account_balance` (`account_book_code`, `fiscal_year`, `period_number`, `account_code`, `currency_code`) USING BTREE,
  KEY `idx_fiscal_year_period` (`fiscal_year`, `period_number`) USING BTREE,
  KEY `idx_account_code` (`account_code`) USING BTREE,
  KEY `idx_account_book_fiscal_year` (`account_book_code`, `fiscal_year`) USING BTREE,
  KEY `idx_currency_code` (`currency_code`) USING BTREE,
  CONSTRAINT `fk_gl_account_balance_account_book_fiscal_year` FOREIGN KEY (`account_book_code`, `fiscal_year`) REFERENCES `account_book_fiscal_year` (`account_book_code`, `fiscal_year`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='科目余额表，对应 GL.xml 科目余额，按账套+年度+期间+科目+币种';

SET FOREIGN_KEY_CHECKS = 1;
