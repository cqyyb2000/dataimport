# Linux Docker 部署说明

将 **前端静态资源（Nginx）**、**Flask 后端（Gunicorn）**、**MySQL 8** 一键编排部署。  
MySQL 数据、上传文件、日志均通过 **bind mount** 落到宿主机物理盘 `/home/mysqldata/`（可在 `.env` 中改 `DATA_ROOT`）。

## 目录结构

```text
docs/docker/
├── docker-compose.yml      # 编排
├── .env.example            # 环境变量模板 → 复制为 .env
├── README.md               # 本说明
├── backend/
│   ├── Dockerfile
│   └── docker-entrypoint.sh   # 按环境变量生成 set.config 并启动 gunicorn
├── frontend/
│   └── Dockerfile             # 多阶段：npm build → nginx 镜像
└── nginx/
    ├── nginx.conf
    └── default.conf           # / → 前端；/api/ → 后端；/uploads/ → 宿主机
```

仓库根目录另有 `.dockerignore`，减小构建上下文。

## 宿主机准备

```bash
sudo mkdir -p /home/mysqldata/{mysql,uploads,logs/nginx,backups}
# MySQL 官方镜像默认以 uid/gid 999 运行
sudo chown -R 999:999 /home/mysqldata/mysql
sudo chmod 750 /home/mysqldata/mysql
# 上传与日志目录给容器写（backend 以 root 跑时可先 755；若后续改非 root 再收紧权限）
sudo chmod -R 755 /home/mysqldata/uploads /home/mysqldata/logs
```

依赖：Docker Engine + Docker Compose v2。

> **部署机无外网？** 不要在服务器上 `build`/`pull`。请先在有网的 Windows 上导出镜像，再拷到 Ubuntu 加载。详见 [OFFLINE.md](./OFFLINE.md)。

## 配置与启动

在 **本目录**（`docs/docker`）操作：

```bash
cd /path/to/repo/docs/docker
cp .env.example .env
vi .env   # 务必修改 MYSQL_*、SECRET_KEY、JWT_SECRET_KEY

docker compose up -d --build
docker compose ps
docker compose logs -f --tail=100
```

浏览器访问：`http://服务器IP/`（端口由 `.env` 的 `HTTP_PORT` 控制，默认 80）。

## 数据持久化说明

| 宿主机路径 | 容器内路径 | 说明 |
|------------|------------|------|
| `/home/mysqldata/mysql` | `/var/lib/mysql` | MySQL 数据文件（核心） |
| `/home/mysqldata/uploads` | `/app/uploads`（后端）与 Nginx 只读挂载 | 业务上传 |
| `/home/mysqldata/logs` | `/app/logs` | 后端日志 |
| `/home/mysqldata/logs/nginx` | `/var/log/nginx` | Nginx 日志 |

**不要用 Docker named volume 存库**：在 Linux 上 named volume 也在 Docker 目录下；本方案使用宿主机绝对路径 bind mount，数据始终在你指定的盘上。

`dataimport.sql` 仅在 **mysql 数据目录为空** 时由官方入口脚本执行一次。若目录里已有库文件，不会再次导入。

## 常用命令

```bash
# 停止 / 启动
docker compose stop
docker compose start

# 重建后端或前端
docker compose up -d --build backend
docker compose up -d --build nginx

# 查看日志
docker compose logs -f backend
docker compose logs -f mysql

# 备份库（示例）
docker compose exec mysql \
  mysqldump -u root -p"$MYSQL_ROOT_PASSWORD" dataimport \
  > /home/mysqldata/backups/dataimport_$(date +%F).sql
```

注意：上面备份命令中的密码请从 `.env` 读取，或先 `export $(grep -v '^#' .env | xargs)`。

## 配置对应关系

- 前端构建参数：`VUE_APP_API_BASE_URL=/api`（同域，经 Nginx 反代）
- 后端容器内：`DB_HOST=mysql`（Compose 服务名），由 `docker-entrypoint.sh` 写入 `set.config`
- `.env` 中的 `MYSQL_USER` / `MYSQL_PASSWORD` / `MYSQL_DATABASE` 必须与后端使用的库账号一致（入口脚本已从同一组环境变量生成）

## 注意事项

1. **生产务必改密码和密钥**，不要使用 `.env.example` 中的占位值。  
2. 若 MySQL 容器反复重启，先查权限：`ls -la /home/mysqldata/mysql`，确认属主为 `999:999`。  
3. 已有数据目录时，不要删除 `/home/mysqldata/mysql` 除非确认可丢库。  
4. 防火墙放行 `HTTP_PORT`（默认 80）；一般不必对公网开放 3306。  
5. 修改 Nginx 配置后：`docker compose restart nginx`。  
6. 修改前端代码后需重新构建 nginx 镜像：`docker compose up -d --build nginx`。

## 架构示意

```text
浏览器 → :80 nginx
           ├─ /          前端 dist
           ├─ /api/      → backend:5000（Gunicorn + Flask）
           └─ /uploads/  → /home/mysqldata/uploads
         backend → mysql:3306
                    └─ 数据 → /home/mysqldata/mysql
```
