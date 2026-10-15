# Windows 部署指南（非 Docker）

本文说明在 **Windows Server / Windows 10/11** 上，**不使用 Docker**，直接部署本系统的前端与后端。

| 组件 | 技术 | 生产建议 |
|------|------|----------|
| 后端 | Flask + **Waitress** | `python run_waitress.py`，可用 NSSM 注册服务 |
| 前端 | Vue 3 构建产物 `dist` | IIS 或 Nginx for Windows 托管静态文件 |
| 数据库 | MySQL 5.7+ / 8.x | 本机或内网实例，`utf8mb4` |

> Linux + Docker 部署见 [docs/docker/README.md](./docker/README.md)。  
> Windows 上**不要**使用 gunicorn（面向 Linux）；生产以 Waitress 为准。

---

## 1. 架构与端口

```text
浏览器
  │
  ├─ 前端静态页  →  IIS / Nginx（如 :80）
  │
  └─ API 请求    →  http://服务器IP:5501/api
                      │
                      ▼
                 Flask + Waitress
                      │
                      ▼
                   MySQL :3306
```

| 组件 | 默认端口 | 配置位置 |
|------|----------|----------|
| 后端 API | `5501` | `backend/set.config` → `[APPLICATION] PORT` |
| 前端站点 | `80` / `443` | IIS 站点绑定 / Nginx `listen` |
| MySQL | `3306` | MySQL 与 `set.config` → `[DATABASE]` |
| 前端开发服 | `9093` | 仅开发：`frontend/vue.config.js`（生产不用） |

前端构建时必须指定 API 地址，且**以 `/api` 结尾**，例如：

```text
VUE_APP_API_BASE_URL=http://192.168.1.100:5501/api
```

与 `frontend/src/api/index.js` 约定一致。

---

## 2. 环境准备

### 2.1 系统

- Windows Server 2016+，或 Windows 10/11 64 位  
- 建议使用**管理员**账号完成安装、防火墙、NSSM 服务注册  

### 2.2 Python

1. 安装 [Python 3.10+](https://www.python.org/downloads/)（建议 3.11 或 3.12）  
2. 安装时勾选 **Add python.exe to PATH**  
3. 验证：

```powershell
python --version
pip --version
```

### 2.3 Node.js（仅构建前端时需要）

生产服务器若只托管已构建好的 `dist`，可不必安装 Node。  
在本机或构建机上：

1. 安装 [Node.js LTS](https://nodejs.org/)（建议 18.x / 20.x）  
2. 验证：`node --version`、`npm --version`  

### 2.4 MySQL

1. 安装 MySQL 5.7+ 或 8.x，字符集建议 **utf8mb4**  
2. 创建库（名称与 `set.config` 中 `DB_NAME` 一致，默认 `dataimport`）  
3. 导入结构/数据，优先使用仓库根目录的 **`dataimport.sql`**；亦可按需使用 `backend/数据库脚本/` 下脚本  

```powershell
# 示例：命令行导入（按本机 mysql 路径调整）
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS dataimport DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p dataimport < D:\dataimport\dataimport.sql
```

---

## 3. 后端部署

示例目录：`D:\dataimport\backend`（可按实际修改，下文以该路径为例）。

### 3.1 放置代码与配置

1. 将仓库中的 **`backend`** 整目录复制到服务器（如 `D:\dataimport\backend`）。  
2. 编辑同目录下的 **`set.config`**：

| 段 | 关键项 | 说明 |
|----|--------|------|
| `[DATABASE]` | `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` | 与 MySQL 一致；本机可用 `127.0.0.1` 或 `localhost` |
| `[SECURITY]` | `SECRET_KEY`、`JWT_SECRET_KEY` | **生产必须改为足够长的随机串** |
| `[APPLICATION]` | `HOST`、`PORT`、`DEBUG` | 生产：`HOST=0.0.0.0`，`PORT=5501`，`DEBUG=off` |
| `[UPLOAD]` | `UPLOAD_FOLDER` 等 | 默认 `uploads`，相对 backend 目录 |
| `[LOGGING]` | `LOG_FILE` | 默认 `logs/app.log`，确保目录可写 |

3. 手动创建目录（可选，程序也会尝试创建）：

```powershell
mkdir D:\dataimport\backend\logs
mkdir D:\dataimport\backend\uploads
```

### 3.2 虚拟环境与依赖

```powershell
cd D:\dataimport\backend
python -m venv venv
.\venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

国内网络可加速：

```powershell
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

说明：

- 生产以 **Waitress** 为准；若 `pip install` 在 **gunicorn** 上报错，可暂时从 `requirements.txt` 中注释掉 gunicorn 再安装。  
- **无外网**：使用仓库内已打好的 `backend/offline_packages/`（Windows + Python 3.12）。详见该目录 [README.md](../backend/offline_packages/README.md)，或执行：

```powershell
cd D:\dataimport\backend
.\scripts\install_offline_deps.ps1
```

### 3.3 启动（Waitress）

在 **backend** 目录、已激活 venv：

```powershell
python run_waitress.py
```

- 地址/端口：优先环境变量 `WAITRESS_HOST`、`WAITRESS_PORT`，否则读 `set.config` 的 `[APPLICATION]`  
- 线程数：`WAITRESS_THREADS`（默认 `4`）  

```powershell
$env:WAITRESS_THREADS = "8"
python run_waitress.py
```

浏览器或本机测试：`http://127.0.0.1:5501/api/...`（具体路径以接口为准）。

**不要用** `python app.py` 做生产（Flask 内置服务器仅适合本地调试）。

### 3.4 防火墙

放行后端端口入站（示例 5501），否则其他机器无法访问 API：

```powershell
# 管理员 PowerShell 示例
New-NetFirewallRule -DisplayName "DataImport API 5501" -Direction Inbound -Protocol TCP -LocalPort 5501 -Action Allow
```

### 3.5 注册为 Windows 服务（NSSM，推荐）

便于开机自启、崩溃重启。

1. 下载 [NSSM](https://nssm.cc/download)，解压后记下 `nssm.exe` 路径（如 `D:\dataimport\nssm.exe`）。  
2. 确认已按 3.2 建好 `D:\dataimport\backend\venv`。  
3. 编辑 `backend\scripts\install_nssm_service.bat`：  
   - `BACKEND_ROOT`（默认 `D:\dataimport\backend`）  
   - `NSSM`（指向本机 `nssm.exe`）  
4. **以管理员身份运行**该 bat，然后：

```powershell
net start DataImportBackend
```

5. 卸载：管理员运行 `backend\scripts\uninstall_nssm_service.bat`。  
6. 若参数曾配错，可用 `backend\scripts\fix_nssm_use_run_waitress.bat` 改回 `run_waitress.py`。

手工等价配置：

| NSSM 项 | 值 |
|---------|-----|
| Path | `D:\dataimport\backend\venv\Scripts\python.exe` |
| Arguments | `D:\dataimport\backend\run_waitress.py` |
| Startup directory | `D:\dataimport\backend` |

**注意**：参数不要写成带外层引号的整段 `-m waitress --port=5501 app:app`，否则可能报 `No module named waitress --port=...`。推荐直接用 `run_waitress.py`。

服务日志还可看：`backend\logs\nssm_stdout.log`、`nssm_stderr.log`（脚本已配置）。

---

## 4. 前端部署

### 4.1 构建静态资源

在能访问 Node 的机器上（可为本机）：

```powershell
cd D:\dataimport\frontend
npm ci
```

生产 API 地址：新建或编辑 **`frontend\.env.production`**（推荐，避免改开发用 `.env`）：

```text
VUE_APP_API_BASE_URL=http://你的服务器IP或域名:5501/api
```

构建：

```powershell
npm run build
```

产物目录：`frontend\dist`。将该目录整体部署到 Web 服务器站点根目录。

### 4.2 用 IIS 托管（常见）

1. 启用 IIS，并安装 **URL Rewrite**（Vue `history` 路由需要）。  
2. 新建站点，物理路径指向 `dist`（如 `D:\dataimport\frontend\dist`）。  
3. 绑定端口 `80`（或指定主机头/HTTPS）。  
4. 在 `dist` 根目录放置 `web.config`，避免刷新子路由 404，示例：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <rewrite>
      <rules>
        <rule name="VueHistory" stopProcessing="true">
          <match url=".*" />
          <conditions logicalGrouping="MatchAll">
            <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
            <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
          </conditions>
          <action type="Rewrite" url="/index.html" />
        </rule>
      </rules>
    </rewrite>
    <staticContent>
      <clientCache cacheControlMode="UseMaxAge" cacheControlMaxAge="7.00:00:00" />
    </staticContent>
  </system.webServer>
</configuration>
```

说明：后端 `backend/web.config` 面向旧版 FastCGI，**不要**拿来当前端站点配置。

### 4.3 用 Nginx for Windows 托管（可选）

安装 [Nginx for Windows](https://nginx.org/en/download.html)，站点配置要点：

```nginx
server {
    listen 80;
    server_name _;
    root D:/dataimport/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

前后端若要用**同一域名**反代（前端 `/`、API `/api`），可在 Nginx 增加：

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:5501;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    client_max_body_size 100M;
    proxy_read_timeout 300s;
}
```

此时前端构建可改为：

```text
VUE_APP_API_BASE_URL=/api
```

### 4.4 跨域

后端已启用 **Flask-CORS**。前后端不同源（例如前端 `:80`、API `:5501`）时，一般可直接访问；若浏览器报 CORS，再检查网关或 CORS 配置。同源反代（上一节）可避免跨域问题。

### 4.5 仅开发调试前端（非生产）

```powershell
cd frontend
npm run serve
```

默认端口见 `vue.config.js`（当前为 `9093`）。`.env` / `.env.development` 中的 `VUE_APP_API_BASE_URL` 指向可访问的后端即可。

---

## 5. 推荐目录布局（示例）

```text
D:\dataimport\
├── backend\                 # Flask 后端
│   ├── set.config
│   ├── venv\
│   ├── uploads\
│   ├── logs\
│   ├── run_waitress.py
│   └── scripts\             # NSSM 安装/卸载脚本
├── frontend\
│   └── dist\                # 构建产物 → IIS/Nginx 站点根
├── dataimport.sql           # 库初始化（从仓库根拷贝）
└── nssm.exe                 # 可选
```

---

## 6. 部署检查清单

- [ ] MySQL 已建库并导入 `dataimport.sql`（或等价脚本），账号与 `set.config` 一致  
- [ ] `set.config` 中库密码、JWT/SECRET 已改为生产值；`DEBUG=off`  
- [ ] `backend\logs`、`uploads` 可写  
- [ ] venv 内 `pip install -r requirements.txt` 成功；`python run_waitress.py` 可访问  
- [ ] 防火墙已放行 `5501`（及前端 `80`/`443`）  
- [ ] 前端 `.env.production` 中 `VUE_APP_API_BASE_URL` 以 `/api` 结尾且指向正确主机  
- [ ] `npm run build` 后站点可打开，登录与接口正常  
- [ ] （可选）NSSM 服务 `DataImportBackend` 已设为自动启动  

---

## 7. 常见问题

**无法连接数据库**  
查 MySQL 是否启动、端口、`DB_HOST`、用户权限与密码；本机优先用 `127.0.0.1`。

**前端接口 404 / 前缀错误**  
确认构建时的 `VUE_APP_API_BASE_URL` **以 `/api` 结尾**；改环境变量后需重新 `npm run build`。

**刷新页面 404（Vue 路由）**  
IIS 需 URL Rewrite + `web.config`；Nginx 需 `try_files ... /index.html`。

**Waitress / 模块导入失败**  
确认使用 **venv** 且在 **backend** 目录下启动；NSSM 的 Path 必须是 venv 里的 `python.exe`。

**gunicorn 安装失败**  
Windows 可忽略；注释 `requirements.txt` 中 gunicorn 即可，生产用 Waitress。

**上传失败或体积限制**  
`set.config` 中 `MAX_CONTENT_LENGTH` 默认约 100MB；若经 IIS/Nginx 反代，同步调大网关请求体限制。

---

## 8. 相关文件索引

| 路径 | 说明 |
|------|------|
| `backend/requirements.txt` | Python 依赖 |
| `backend/run_waitress.py` | Windows 生产启动入口 |
| `backend/set.config` | 数据库与应用配置 |
| `backend/scripts/install_nssm_service.bat` | 注册 Windows 服务 |
| `backend/数据库脚本/` | 补充 SQL（若有） |
| `dataimport.sql` | 仓库根目录全库脚本 |
| `frontend/package.json` | `build` / `serve` |
| `frontend/.env.production` | 生产 `VUE_APP_API_BASE_URL` |
| `docs/docker/` | Linux Docker 方案（本文不适用） |

---

*文档版本：与当前仓库非 Docker 部署方式一致；配置以 `set.config` 与代码为准。*
