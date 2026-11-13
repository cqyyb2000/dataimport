/*
 报销台账表
 与账套档案分开存放。执行本脚本会删除并重建 bx_ 开头的这五张表。

 顺序：部门、项目、预算、报销单、单据号流水。
 部门、项目的上级外键限制删除仍有下级的档案。
 预算引用部门和项目，报销单引用预算，因此有预算或报销单时不能删除对应档案。
 最明细级、循环上级、单据号只增不减由服务层保证。
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `bx_claim`;
DROP TABLE IF EXISTS `bx_budget`;
DROP TABLE IF EXISTS `bx_doc_seq`;
DROP TABLE IF EXISTS `bx_department`;
DROP TABLE IF EXISTS `bx_project`;

CREATE TABLE `bx_department` (
  `fiscal_year` int NOT NULL COMMENT '年度，4位',
  `dept_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '部门代码，同一年度内唯一',
  `dept_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '部门名称',
  `parent_dept_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '上级部门代码，空表示第一级',
  `level_no` smallint NOT NULL COMMENT '级次，第一级为 1，下级比直接上级大 1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`fiscal_year`, `dept_code`) USING BTREE,
  KEY `idx_bx_department_parent` (`fiscal_year`, `parent_dept_code`) USING BTREE,
  CONSTRAINT `fk_bx_department_parent` FOREIGN KEY (`fiscal_year`, `parent_dept_code`) REFERENCES `bx_department` (`fiscal_year`, `dept_code`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_bx_department_level` CHECK (`level_no` >= 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报销台账部门，按年度多级存放，与账套内设机构无关';

CREATE TABLE `bx_project` (
  `fiscal_year` int NOT NULL COMMENT '年度，4位',
  `project_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '项目代码，同一年度内唯一',
  `project_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '项目名称',
  `parent_project_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '上级项目代码，空表示第一级',
  `level_no` smallint NOT NULL COMMENT '级次，第一级为 1，下级比直接上级大 1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`fiscal_year`, `project_code`) USING BTREE,
  KEY `idx_bx_project_parent` (`fiscal_year`, `parent_project_code`) USING BTREE,
  CONSTRAINT `fk_bx_project_parent` FOREIGN KEY (`fiscal_year`, `parent_project_code`) REFERENCES `bx_project` (`fiscal_year`, `project_code`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_bx_project_level` CHECK (`level_no` >= 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报销台账项目，按年度多级存放，与账套项目档案无关';

CREATE TABLE `bx_budget` (
  `fiscal_year` int NOT NULL COMMENT '年度，4位',
  `dept_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '部门代码',
  `project_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '项目代码',
  `amount` decimal(18, 2) NOT NULL COMMENT '预算金额，大于等于 0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`fiscal_year`, `dept_code`, `project_code`) USING BTREE,
  KEY `idx_bx_budget_project` (`fiscal_year`, `project_code`) USING BTREE,
  CONSTRAINT `fk_bx_budget_department` FOREIGN KEY (`fiscal_year`, `dept_code`) REFERENCES `bx_department` (`fiscal_year`, `dept_code`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_bx_budget_project` FOREIGN KEY (`fiscal_year`, `project_code`) REFERENCES `bx_project` (`fiscal_year`, `project_code`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_bx_budget_amount` CHECK (`amount` >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报销台账预算，年度+部门+项目唯一';

CREATE TABLE `bx_claim` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '内部主键',
  `doc_no` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '单据号，年度4位+月份2位+流水4位',
  `fiscal_year` int NOT NULL COMMENT '所属年度，与报销时间的年份一致',
  `expense_date` date NOT NULL COMMENT '报销时间，精确到日期',
  `dept_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '部门代码',
  `project_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '项目代码',
  `claimant` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '报销人',
  `summary` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '摘要',
  `amount` decimal(18, 2) NOT NULL COMMENT '报销金额，大于 0',
  `status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '状态：待支出、已计入',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `uk_bx_claim_doc_no` (`doc_no`) USING BTREE,
  KEY `idx_bx_claim_budget` (`fiscal_year`, `dept_code`, `project_code`) USING BTREE,
  KEY `idx_bx_claim_expense_date` (`expense_date`) USING BTREE,
  KEY `idx_bx_claim_status` (`status`) USING BTREE,
  CONSTRAINT `fk_bx_claim_budget` FOREIGN KEY (`fiscal_year`, `dept_code`, `project_code`) REFERENCES `bx_budget` (`fiscal_year`, `dept_code`, `project_code`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_bx_claim_amount` CHECK (`amount` > 0),
  CONSTRAINT `chk_bx_claim_status` CHECK (`status` IN ('待支出', '已计入'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报销台账报销单';

CREATE TABLE `bx_doc_seq` (
  `fiscal_year` int NOT NULL COMMENT '年度，4位',
  `fiscal_month` tinyint NOT NULL COMMENT '月份，1到12',
  `max_seq` int NOT NULL DEFAULT 0 COMMENT '该年月已发出的最大流水号，0到9999',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`fiscal_year`, `fiscal_month`) USING BTREE,
  CONSTRAINT `chk_bx_doc_seq_month` CHECK (`fiscal_month` BETWEEN 1 AND 12),
  CONSTRAINT `chk_bx_doc_seq_max` CHECK (`max_seq` BETWEEN 0 AND 9999)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报销单据号流水，按报销时间的年月分别编号';

SET FOREIGN_KEY_CHECKS = 1;
