import Mock from 'mockjs';

// 模拟用户数据
Mock.mock('/api/users', 'get', {
  code: 200,
  data: [
    { id: 1, username: 'admin', password: 'admin' },
    // 更多用户数据...
  ],
});

// 模拟菜单数据
Mock.mock('/api/menus', 'get', {
  code: 200,
  data: [
    {
      "name": "系统管理",
      "path": "/system",
      "icon": "el-icon-setting",
      "children": [
        {
          "name": "用户管理",
          "path": "/system/users",
          "icon": "el-icon-user",
          "children": []
        },
        {
          "name": "菜单管理",
          "path": "/system/menus",
          "icon": "el-icon-menu",
          "children": []
        },
        {
          "name": "权限管理",
          "path": "/system/permissions",
          "icon": "el-icon-lock",
          "children": []
        },
        {
          "name": "系统设置",
          "path": "/system/settings",
          "icon": "el-icon-lock",
          "children": []
        }
      ]
    },
    {
      "name": "档案管理",
      "path": "/documents",
      "icon": "el-icon-lock",
      "children": [
        {
          "name": "档案目录",
          "path": "/documents/catalog",
          "component": "doc/DocCatalog",
          "icon": "el-icon-menu",
          "children": []
        },
        {
          "name": "档案查询",
          "path": "/documents/query",
          "component": "doc/DocQuery",
          "icon": "el-icon-search",
          "children": []
        }
      ]
    }
  ]
  ,
});

// 模拟登录接口
Mock.mock('/api/login', 'post', (options) => {
  const { username, password } = JSON.parse(options.body);
  if (username === 'admin' && password === 'admin') {
    return {
      code: 200,
      success: true,
      message: '登录成功',
      data: {
        token: 'mock-token', // 模拟的 token
        userId: 1,
      },
    };
  } else {
    return {
      code: 401,
      success: false,
      message: '用户名或密码错误',
    };
  }
});

// 其他模拟API...

// 模拟档案目录数据
let catalogData = [
  { autoid: 1, nodename: '项目1', parentid: 0, keyname: '项目名称' },
  { autoid: 2, nodename: '2025年', parentid: 1, keyname: '年' },
  { autoid: 3, nodename: '1月', parentid: 1, keyname: '月' },
  { autoid: 4, nodename: '1期', parentid: 3, keyname: '期' },
  { autoid: 5, nodename: '2期', parentid: 3, keyname: '期' },
  { autoid: 6, nodename: '上', parentid: 4, keyname: '上' },
  { autoid: 7, nodename: '2号', parentid: 4, keyname: '号' },
  { autoid: 8, nodename: '1号', parentid: 5, keyname: '号' }
];

// 获取档案目录
Mock.mock('/api/doccatalog', 'get', {
  code: 200,
  data: catalogData
});

// 创建档案目录节点
Mock.mock('/api/doccatalog', 'post', (options) => {
  const newNode = JSON.parse(options.body);
  const newId = Math.max(...catalogData.map(item => item.autoid)) + 1;
  const node = {
    autoid: newId,
    ...newNode
  };
  catalogData.push(node);
  return {
    code: 200,
    data: node,
    message: '创建成功'
  };
});

// 更新档案目录节点
Mock.mock(/\/api\/doccatalog\/\d+/, 'put', (options) => {
  const catalogId = parseInt(options.url.split('/').pop());
  const updatedData = JSON.parse(options.body);
  const index = catalogData.findIndex(item => item.autoid === catalogId);
  if (index !== -1) {
    catalogData[index] = { ...catalogData[index], ...updatedData };
    return {
      code: 200,
      data: catalogData[index],
      message: '更新成功'
    };
  }
  return {
    code: 404,
    message: '节点不存在'
  };
});

// 删除档案目录节点
Mock.mock(/\/api\/doccatalog\/\d+/, 'delete', (options) => {
  const catalogId = parseInt(options.url.split('/').pop());
  
  // 递归删除所有子节点
  const deleteNodeAndChildren = (nodeId) => {
    const children = catalogData.filter(item => item.parentid === nodeId);
    children.forEach(child => deleteNodeAndChildren(child.autoid));
    catalogData = catalogData.filter(item => item.autoid !== nodeId);
  };
  
  deleteNodeAndChildren(catalogId);
  
  return {
    code: 200,
    message: '删除成功'
  };
});
