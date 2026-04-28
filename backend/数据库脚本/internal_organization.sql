/*
 内设机构表 internal_organization
 与账套号、会计年度关联，公共档案按账套+年度维度存储
 依据 GB/T 24589.2-2010 及 XML <内设机构> 结构设计

 XML 对应：
   <内设机构编码> -> internal_org_code
   <内设机构名称> -> internal_org_name
   <上级机构编码> -> parent_org_code

 关系：依赖 account_book_fiscal_year（账套+年度），同一账套同一年度下内设机构编码唯一

 Date: 2025-01
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- 内设机构表（按账套+年度）
-- ----------------------------
DROP TABLE IF EXISTS `internal_organization`;

CREATE TABLE `internal_organization` (
  `account_book_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账套编码，外键关联账套年度',
  `fiscal_year` int NOT NULL COMMENT '会计年度，4位如2021',
  `internal_org_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '内设机构编码，对应 XML 内设机构编码',
  `internal_org_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '内设机构名称，对应 XML 内设机构名称',
  `parent_org_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '上级机构编码，对应 XML 上级机构编码',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '备注',
  `status` tinyint(1) DEFAULT 1 COMMENT '状态：1=启用 0=停用',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`account_book_code`, `fiscal_year`, `internal_org_code`) USING BTREE,
  KEY `idx_fiscal_year` (`fiscal_year`) USING BTREE,
  KEY `idx_internal_org_code` (`internal_org_code`) USING BTREE,
  KEY `idx_parent_org_code` (`parent_org_code`) USING BTREE,
  CONSTRAINT `fk_io_account_book_fiscal_year` FOREIGN KEY (`account_book_code`, `fiscal_year`) REFERENCES `account_book_fiscal_year` (`account_book_code`, `fiscal_year`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='内设机构表，按账套+年度，对应 XML 内设机构';

SET FOREIGN_KEY_CHECKS = 1;
