/*
 为已有 users 表增加报销台账角色。
 accountant = 会计，cashier = 出纳。管理员不依赖该字段，保持为空。
 列已存在时本脚本不重复添加。
*/

SET @role_exists := (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'users'
    AND COLUMN_NAME = 'role'
);

SET @add_role_sql := IF(
  @role_exists = 0,
  'ALTER TABLE `users` ADD COLUMN `role` varchar(20) NULL DEFAULT NULL COMMENT ''报销台账角色：accountant=会计，cashier=出纳；管理员可为空'' AFTER `is_admin`',
  'SELECT ''users.role already exists'''
);

PREPARE add_role_stmt FROM @add_role_sql;
EXECUTE add_role_stmt;
DEALLOCATE PREPARE add_role_stmt;
