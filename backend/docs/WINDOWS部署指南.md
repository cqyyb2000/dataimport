# Windows 服务器部署指南

本文说明在 **Windows Server / Windows 10+** 上部署本系统 **后端（Flask）** 与 **前端（Vue 3）** 的推荐流程。后端使用 **Waitress** 作为 WSGI 服务器（适合 Windows）；**gunicorn** 面向 Linux，Windows 上不必使用。

---

## 1. 架构与端口（示例）

| 组件 | 说明 | 默认端口（以 `set.config` / 前端环境变量为准） |
|------|------|-----------------------------------------------|
| 后端 API | Flask + Waitress | `5501`（`[APPLICATION] PORT`） |
| 前端开发服 | `npm run serve` | `8066`（仅开发） |
| 前端生产 | 静态文件由 IIS / Nginx 等托管 | `80` / `443` 等 |
| MySQL | 数据库 | `3306` |

前端通过 `VUE_APP_API_BASE_URL` 访问后端，例如：`http://服务器IP:5501/api`（末尾 **必须带 `/api`**，与 `src/api/index.js` 一致）。

---

## 2. 环境准备

### 2.1 操作系统与权限

- Windows Server 2016+ 或 Windows 10/11 64 位。
- 准备 **管理员权限**（安装组件、开放防火墙、注册服务时可能需要）。

### 2.2 Python

1. 安装 [Python 3.10+](https://www.python.org/downloads/)（建议 3.11 或 3.12）。
2. 安装时勾选 **Add python.exe to PATH**。
3. 验证：`python --version`、`pip --version`。

### 2.3 Node.js（仅构建前端需要）

1. 安装 [Node.js LTS](https://nodejs.org/)（建议 18.x / 20.x）。
2. 验证：`node --version`、`npm --version`。

### 2.4 MySQL

1. 安装 MySQL 5.7+ 或 8.x，字符集建议使用 **utf8mb4**。
2. 创建数据库（名称与 `set.config` 中 `DB_NAME` 一致，如 `dataimport`）。
3. 导入项目内 **`数据库脚本`**（如 `gl_tables.sql` 等），保证表结构与业务一致。

---

## 3. 后端部署

### 3.1 目录与配置文件

1. 将 **`backend`** 整目录复制到服务器，例如：`D:\apps\DataImport\backend`。
2. 在 **`backend`** 目录下维护 **`set.config`**（与 `app.py` 同级），按环境修改：
   - **`[DATABASE]`**：主机、端口、用户、密码、库名（**生产务必使用强密码**）。
   - **`[SECURITY]`**：`SECRET_KEY`、`JWT_SECRET_KEY`（**生产必须改为随机长字符串**）。
   - **`[APPLICATION]`**：
     - `HOST = 0.0.0.0` 表示监听所有网卡；仅本机可改为 `127.0.0.1`。
     - `PORT = 5501` 与前端 `VUE_APP_API_BASE_URL` 中的端口一致。
     - 生产建议 **`DEBUG = off`**（若 `config_reader` 使用 `getboolean`，请按实际键值填写）。
   - **`[LOGGING]`**：确保 **`logs`** 目录可写（首次运行可手动创建 `backend\logs`）。

### 3.2 虚拟环境与依赖

在 **CMD** 或 **PowerShell** 中：

```powershell
cd D:\apps\DataImport\backend
python -m venv venv
.\venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

若下载慢，可使用镜像：

```powershell
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3.3 使用 Waitress 启动（推荐）

在 **`backend`** 目录、已激活虚拟环境：

```powershell
python run_waitress.py
```

- 监听地址与端口优先读环境变量 **`WAITRESS_HOST`**、**`WAITRESS_PORT`**，否则读取 **`set.config`** 的 `[APPLICATION]`。
- 线程数：**`WAITRESS_THREADS`**（默认 `4`）。

示例：

```powershell
set WAITRESS_THREADS=8
python run_waitress.py
```

### 3.4 Windows 防火墙

放行后端端口（例如 **5501**）入站规则，否则其他机器无法访问 API。

### 3.5 可选：注册为 Windows 服务（NSSM）

1. 下载 [NSSM](https://nssm.cc/download)，解压后记住 `win64\nssm.exe` 路径。
2. **一键脚本（推荐）**：仓库内 `backend\scripts\install_nssm_service.bat`  
   - 默认后端目录为 `D:\dataimport\backend`，服务名 `DataImportBackend`。  
   - 用记事本打开脚本，将 `NSSM=C:\nssm\win64\nssm.exe` 改成你机器上的实际路径。  
   - **以管理员身份运行** 该 bat，完成后执行 `net start DataImportBackend`。  
   - 卸载：`backend\scripts\uninstall_nssm_service.bat`（同样需管理员，且与安装脚本中的 NSSM 路径一致）。
3. **手工配置**（与脚本等价）：将服务指向：`D:\dataimport\backend\venv\Scripts\python.exe`  
   参数：`D:\dataimport\backend\run_waitress.py`  
   启动目录：`D:\dataimport\backend`  
   **与旧项目 NSSM 习惯对照**：若以前用「Path = 系统 Python、参数 = `-m waitress --port=5000 app:app`、启动目录 = 项目根」，这里只需把 Path 换成 **venv 里的 `python.exe`**，启动目录改为 **`D:\dataimport\backend`**，参数可二选一：  
   - **推荐**：`run_waitress.py`（会 `setup_logging`，端口优先读配置 / 环境变量 `WAITRESS_PORT`，默认 5501）；  
   - **或** 与旧项目相同写法：`-m waitress --port=5501 app:app`（`app:app` 仍指向本仓库 `app.py` 中的 `app`）。  
     **注意**：NSSM 的「参数」里**不要**给整段 `-m waitress ...` 再加一层外层引号，也不要在 `nssm install` 时把第三个参数写成 `" -m waitress --port=5501 app:app "` 一整串；否则 Python 会报 `No module named waitress --port=5501 app:app`（把整句当成了 `-m` 的模块名）。图形界面里「参数」各行/各词按 NSSM 默认拆分即可。若已配错，可**管理员**运行 `backend\scripts\fix_nssm_use_run_waitress.bat` 改回 `run_waitress.py`。
4. 服务恢复策略、开机自启可在 NSSM 或服务管理器中调整；脚本已设置自动启动与退出后延迟重启。

### 3.6 开发方式说明（不推荐用于生产）

`python app.py` 使用 Flask 内置开发服务器，仅适合本地调试；**生产请使用 `run_waitress.py`**。

---

## 4. 前端部署

### 4.1 构建静态资源

在 **`frontend`** 目录：

```powershell
cd D:\apps\DataImport\frontend
npm ci
```

生产环境 API 地址在 **`.env.production`**（推荐）或构建前设置环境变量：

```text
VUE_APP_API_BASE_URL=http://你的服务器IP或域名:5501/api
```

执行构建：

```powershell
npm run build
```

产物在 **`frontend\dist`**，将该目录部署到 **IIS**、**Nginx for Windows** 或任意静态站点服务器。

### 4.2 与后端跨域

后端已使用 **Flask-CORS**；若前后端 **同源**（例如同一域名不同路径由反向代理合并），一般无额外问题。若前端静态页与 API **不同源**，需确认浏览器控制台无 CORS 报错，必要时在网关或 Flask CORS 配置中收紧/放行来源。

### 4.3 仅内网调试前端（可选）

```powershell
npm run serve
```

默认开发端口见 **`vue.config.js`**（如 `8066`），此时 `.env` 中 `VUE_APP_API_BASE_URL` 应指向可访问的后端地址。

---

## 5. 部署检查清单

- [ ] MySQL 已创建库并导入脚本，账号与 `set.config` 一致。
- [ ] `set.config` 中数据库密码、JWT 密钥已改为生产值；`DEBUG` 已关闭（如适用）。
- [ ] `backend\logs` 可写，`uploads` 上传目录存在或可自动创建。
- [ ] `pip install -r requirements.txt` 无报错，`python run_waitress.py` 可启动。
- [ ] 防火墙已放行后端端口。
- [ ] 前端 `VUE_APP_API_BASE_URL` 指向 `http://主机:端口/api`，构建后登录与接口请求正常。

---

## 6. 常见问题

**无法连接数据库**  
检查 MySQL 是否监听、防火墙、`DB_HOST`（本机可用 `127.0.0.1` 或 `localhost`）、用户远程权限。

**前端 404 或接口前缀错误**  
确认 `VUE_APP_API_BASE_URL` **以 `/api` 结尾**，与后端蓝图前缀一致。

**Waitress / 依赖导入报错**  
确认使用 **虚拟环境** 且已执行 `pip install -r requirements.txt`；在 **`backend`** 目录下运行 `run_waitress.py`。

**gunicorn**  
Windows 上不必安装或使用；若 `pip install` 在 gunicorn 上报错，可暂时从 `requirements.txt` 中注释 gunicorn 再安装，**生产以 Waitress 为准**。

---

## 7. 文档与脚本索引

| 路径 | 说明 |
|------|------|
| `backend/requirements.txt` | Python 依赖 |
| `backend/run_waitress.py` | Windows 推荐启动入口 |
| `backend/set.config` | 数据库与应用配置 |
| `backend/数据库脚本/` | 表结构等 SQL |
| `frontend/package.json` | 前端脚本 `build` / `serve` |
| `frontend/.env` / `.env.production` | `VUE_APP_API_BASE_URL` |

---

*文档版本：与当前仓库结构一致；若配置项变更，请以代码与 `set.config` 示例为准。*
