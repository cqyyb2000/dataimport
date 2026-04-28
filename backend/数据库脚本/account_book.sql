/*
 账套信息表（主表）account_book
 账套—会计年度表（从表）account_book_fiscal_year
 依据 XML <电子账簿> 结构设计，会计年度单独分离，与账套表为主从关系

 XML 对应：
   <电子账簿编号> -> account_book_code
   <电子账簿名称> -> account_book_name
   <会计核算单位> -> accounting_entity
   ...（不含<会计年度>，会计年度在从表）

 Date: 2025-01
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- 从表先删（主从关系）
-- ----------------------------
DROP TABLE IF EXISTS `account_book_fiscal_year`;
DROP TABLE IF EXISTS `account_book`;

-- ----------------------------
-- 主表：账套信息（与 XML 电子账簿一一对应，不含会计年度）
-- ----------------------------
CREATE TABLE `account_book` (
  `account_book_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账套编码，对应电子账簿编号',
  `account_book_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账套名称，对应电子账簿名称',
  `accounting_entity` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '会计核算单位',
  `organization_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '组织机构代码',
  `unit_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '单位类型：行政单位/事业单位',
  `industry` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '行业',
  `administrative_division_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '行政区划代码',
  `budget_management_level` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '预算管理级次',
  `funding_source` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '经费来源',
  `developer` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '开发单位',
  `version` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '版本号',
  `base_currency` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '本位币',
  `standard_version` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '标准版本号',
  `default_fiscal_year` int DEFAULT NULL COMMENT '默认展示年度（仅界面用，会计年度数据在从表）',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '备注',
  `status` tinyint(1) DEFAULT 1 COMMENT '状态：1=启用 0=停用',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`account_book_code`) USING BTREE,
  KEY `idx_accounting_entity` (`accounting_entity`(100)) USING BTREE,
  KEY `idx_status` (`status`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='账套信息表（主表），对应 XML 电子账簿，不含会计年度';

-- ----------------------------
-- 从表：账套—会计年度（主从关系，会计年度单独分离）
-- ----------------------------
CREATE TABLE `account_book_fiscal_year` (
  `account_book_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账套编码，外键关联主表',
  `fiscal_year` int NOT NULL COMMENT '会计年度，4位如2021',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '首次导入该年度的时间',
  PRIMARY KEY (`account_book_code`, `fiscal_year`) USING BTREE,
  KEY `idx_fiscal_year` (`fiscal_year`) USING BTREE,
  CONSTRAINT `fk_abfy_account_book` FOREIGN KEY (`account_book_code`) REFERENCES `account_book` (`account_book_code`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='账套—会计年度（从表），主从关系';

SET FOREIGN_KEY_CHECKS = 1;
