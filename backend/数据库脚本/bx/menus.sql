/*
 报销台账菜单。已有库可重复执行。
 会计登录后看到五个页面，出纳只看到报销明细和单位报销统计。
 管理员沿用原逻辑，能看到全部菜单。
*/

INSERT INTO `menus` (`name`, `component`, `parent_id`, `path`, `icon`, `sort_order`)
SELECT '报销台账', '', 0, '', 'Wallet', 40
WHERE NOT EXISTS (
  SELECT 1 FROM `menus` WHERE `name` = '报销台账' AND `parent_id` = 0
);

INSERT INTO `menus` (`name`, `component`, `parent_id`, `path`, `icon`, `sort_order`)
SELECT '部门与项目', 'bx/DepartmentProject', parent_menu.id, '/bx/archive', 'OfficeBuilding', 1
FROM `menus` parent_menu
WHERE parent_menu.name = '报销台账' AND parent_menu.parent_id = 0
  AND NOT EXISTS (SELECT 1 FROM `menus` WHERE `component` = 'bx/DepartmentProject');

INSERT INTO `menus` (`name`, `component`, `parent_id`, `path`, `icon`, `sort_order`)
SELECT '预算', 'bx/Budget', parent_menu.id, '/bx/budget', 'Coin', 2
FROM `menus` parent_menu
WHERE parent_menu.name = '报销台账' AND parent_menu.parent_id = 0
  AND NOT EXISTS (SELECT 1 FROM `menus` WHERE `component` = 'bx/Budget');

INSERT INTO `menus` (`name`, `component`, `parent_id`, `path`, `icon`, `sort_order`)
SELECT '报销录入', 'bx/ClaimEntry', parent_menu.id, '/bx/entry', 'Edit', 3
FROM `menus` parent_menu
WHERE parent_menu.name = '报销台账' AND parent_menu.parent_id = 0
  AND NOT EXISTS (SELECT 1 FROM `menus` WHERE `component` = 'bx/ClaimEntry');

INSERT INTO `menus` (`name`, `component`, `parent_id`, `path`, `icon`, `sort_order`)
SELECT '报销明细', 'bx/ClaimList', parent_menu.id, '/bx/claims', 'List', 4
FROM `menus` parent_menu
WHERE parent_menu.name = '报销台账' AND parent_menu.parent_id = 0
  AND NOT EXISTS (SELECT 1 FROM `menus` WHERE `component` = 'bx/ClaimList');

INSERT INTO `menus` (`name`, `component`, `parent_id`, `path`, `icon`, `sort_order`)
SELECT '单位报销统计', 'bx/ClaimSummary', parent_menu.id, '/bx/summary', 'DataAnalysis', 5
FROM `menus` parent_menu
WHERE parent_menu.name = '报销台账' AND parent_menu.parent_id = 0
  AND NOT EXISTS (SELECT 1 FROM `menus` WHERE `component` = 'bx/ClaimSummary');
