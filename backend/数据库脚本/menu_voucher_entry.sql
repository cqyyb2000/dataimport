-- 凭证录入菜单。已有库执行一次即可。
-- 组件 glvoucher/VoucherEntry 对应前端动态路由；父菜单为「业务处理」(id 22)。

INSERT INTO `menus` (`name`, `component`, `parent_id`, `path`, `icon`, `sort_order`)
SELECT '凭证录入', 'glvoucher/VoucherEntry', parent.id, '/glvoucher/VoucherEntry', 'Edit', 1
FROM `menus` parent
WHERE parent.name = '业务处理'
  AND (parent.component = '' OR parent.component IS NULL)
  AND parent.parent_id = 0
  AND NOT EXISTS (
    SELECT 1 FROM `menus` WHERE `component` = 'glvoucher/VoucherEntry'
  )
LIMIT 1;

-- 已经能看到「凭证列表」的用户，同时能看到「凭证录入」。重新登录后菜单生效。
INSERT INTO `permissions` (`user_id`, `menu_id`)
SELECT p.user_id, entry_menu.id
FROM `permissions` p
JOIN `menus` list_menu ON list_menu.id = p.menu_id AND list_menu.component = 'glvoucher/VoucherList'
JOIN `menus` entry_menu ON entry_menu.component = 'glvoucher/VoucherEntry'
WHERE NOT EXISTS (
  SELECT 1 FROM `permissions` existing
  WHERE existing.user_id = p.user_id AND existing.menu_id = entry_menu.id
);
