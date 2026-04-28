/*
 凭证分录辅助项明细表 gl_voucher_entry_auxiliary
 用于记录有辅助项的分录的辅助核算明细
 对应 GL.xml 记账凭证中的 辅助项1编号~辅助项30编号

 设计说明：
 - 与 gl_voucher_entry 为一对多关系，一条分录可对应多条辅助项记录
 - 仅当分录存在非空辅助项时插入记录
 - auxiliary_item_sequence 对应 XML 中的 辅助项1编号(1)、辅助项2编号(2)...辅助项30编号(30)
 - auxiliary_value 对应 辅助项N编号 的具体取值（如 001、2081101）
 - archive_type 对应档案类型（单位往来、项目、部门、人员、内设机构等），可从 account_auxiliary 关联获取或导入时冗余

 GL.xml 示例：
   <辅助项1编号>001</辅助项1编号>
   <辅助项2编号>2081101</辅助项2编号>
   <辅助项3编号/>

 Date: 2026-02
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- 凭证分录辅助项明细表 gl_voucher_entry_auxiliary
-- ----------------------------
DROP TABLE IF EXISTS `gl_voucher_entry_auxiliary`;

CREATE TABLE `gl_voucher_entry_auxiliary` (
  `account_book_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账套编码，外键关联账套年度',
  `fiscal_year` int NOT NULL COMMENT '会计年度，4位如2021',
  `period_number` tinyint NOT NULL COMMENT '会计期间号，1-12或13',
  `voucher_number` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '凭证编号，外键关联 gl_voucher_entry',
  `entry_line_number` int NOT NULL COMMENT '分录行号，外键关联 gl_voucher_entry',
  `auxiliary_item_sequence` tinyint NOT NULL COMMENT '辅助项序号，1-30，对应 XML 辅助项1编号~辅助项30编号',
  `account_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '科目编号，冗余存储便于按科目查询，对应分录科目',
  `auxiliary_value` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '辅助项取值，对应 XML 辅助项N编号 的具体值',
  `auxiliary_item_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '对应档案类型，如：单位往来、项目、部门、人员、内设机构、个人往来等',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`account_book_code`, `fiscal_year`, `period_number`, `voucher_number`, `entry_line_number`, `auxiliary_item_sequence`) USING BTREE,
  KEY `idx_voucher_entry` (`account_book_code`, `fiscal_year`, `period_number`, `voucher_number`, `entry_line_number`) USING BTREE,
  KEY `idx_account_code` (`account_code`) USING BTREE,
  KEY `idx_auxiliary_value` (`auxiliary_value`) USING BTREE,
  KEY `idx_auxiliary_item_name` (`auxiliary_item_name`) USING BTREE,
  KEY `idx_fiscal_year_period` (`fiscal_year`, `period_number`) USING BTREE,
  CONSTRAINT `fk_gl_voucher_entry_auxiliary_entry` FOREIGN KEY (`account_book_code`, `fiscal_year`, `period_number`, `voucher_number`, `entry_line_number`) REFERENCES `gl_voucher_entry` (`account_book_code`, `fiscal_year`, `period_number`, `voucher_number`, `entry_line_number`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='凭证分录辅助项明细表，记录有辅助项的分录的辅助核算明细';

SET FOREIGN_KEY_CHECKS = 1;
