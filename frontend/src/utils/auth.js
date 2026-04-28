// 导出一个名为 getCurrentUser 的常量函数
export const getCurrentUser = () => {
    // 从浏览器的本地存储中获取键为 'user' 的项，并将其值赋给变量 user
    const user = localStorage.getItem('user');
    //console.log(JSON.parse(user))
    // 如果 user 存在（即不为 null 或 undefined），则将其解析为 JSON 对象并返回
    // 否则返回 null
    return user ? JSON.parse(user) : null;
  };    

// 检查 token 是否过期
export function isTokenExpired() {
  const expiresAt = localStorage.getItem('tokenExpiresAt');
  if (!expiresAt) return true;
  
  const now = new Date().getTime();
  return now >= parseInt(expiresAt);
}

// 检查 token 是否即将过期（比如还有5分钟过期）
export function isTokenExpiringSoon() {
  const expiresAt = localStorage.getItem('tokenExpiresAt');
  if (!expiresAt) return true;
  
  const now = new Date().getTime();
  const fiveMinutes = 5 * 60 * 1000; // 5分钟
  return (parseInt(expiresAt) - now) <= fiveMinutes;
}

// 获取 token
export function getToken() {
  if (isTokenExpired()) {
    // 如果 token 过期，清除所有认证相关的数据
    clearAuthData();
    return null;
  }
  return localStorage.getItem('token');
}

// 更新 token 过期时间
export function updateTokenExpiration() {
  const expiresIn = 30 * 60 * 1000; // 30分钟
  const expiresAt = new Date().getTime() + expiresIn;
  localStorage.setItem('tokenExpiresAt', expiresAt.toString());
}

// 清除认证数据
export function clearAuthData() {
  localStorage.removeItem('token');
  localStorage.removeItem('tokenExpiresAt');
  localStorage.removeItem('user');
  localStorage.removeItem('menus');
}

// 检查是否已登录
export function isAuthenticated() {
  const token = getToken();
  return !!token && !isTokenExpired();
}    

// 设置认证数据
export function setAuthData(token, user, menus) {
  const expiresIn = 30 * 60 * 1000; // 30分钟
  const expiresAt = new Date().getTime() + expiresIn;
  
  localStorage.setItem('token', token);
  localStorage.setItem('tokenExpiresAt', expiresAt.toString());
  localStorage.setItem('user', JSON.stringify(user));
  localStorage.setItem('menus', JSON.stringify(menus));
}    