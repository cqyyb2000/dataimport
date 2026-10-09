# 无外网 Ubuntu 离线部署准备指南

- **推荐准备机**：本机 Windows 里的 **Ubuntu 虚拟机（有外网）** — 与正式环境同系统，deb / 镜像最稳妥  
- **备选准备机**：Windows Docker Desktop（有外网）  
- **部署机**：正式 Ubuntu（无外网）

核心原则：**不要在无网服务器上 build / pull**。  
在有网机器上完成「Docker 的 deb 包 + 打好的 Linux 镜像」，用 U 盘/共享文件夹拷到正式机后 `load` 再启动。

> **版本对齐**：虚拟机 Ubuntu 版本尽量与正式机一致（如都是 22.04 jammy）。可用 `cat /etc/os-release` 两边对照。架构也要一致（常见都是 `amd64`）。

---

## 你需要提前准备的三包东西

```text
offline-bundle/
├── 01-docker-engine/          # Ubuntu 上安装 Docker 的 deb（按系统版本下载）
├── 02-images/                 # 已构建好的容器镜像 tar
│   ├── mysql-8.0.tar
│   ├── dataimport-backend.tar
│   └── dataimport-nginx.tar
└── 03-app/                    # 本仓库（至少含 docs/docker、dataimport.sql、.env）
```

---

## 一、在本机 Ubuntu 虚拟机上准备（推荐）

### 1. 虚拟机里安装 Docker（有网，只装一次）

按 [Docker 官方 Ubuntu 安装文档](https://docs.docker.com/engine/install/ubuntu/) 装好 Engine + Compose 插件，验证：

```bash
docker --version
docker compose version
uname -m   # 应为 x86_64（对应镜像 linux/amd64）
```

### 2. 把项目弄进虚拟机

任选其一：

- VirtualBox/VMware **共享文件夹** 挂上 Windows 上的仓库目录  
- 或 `git clone` / 拷贝整仓到虚拟机  

进入编排目录：

```bash
cd /path/to/repo/docs/docker
```

### 3. 下载 Docker deb（给正式无网机用）

在**虚拟机**里（已能 `apt install docker-ce` 的前提下）：

```bash
mkdir -p offline-bundle/01-docker-engine
cd offline-bundle/01-docker-engine
apt-get download docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
# 若正式机很干净，建议再补常见依赖（按缺包提示继续 download）
cd ../..
```

正式机安装：

```bash
cd offline-bundle/01-docker-engine
sudo dpkg -i *.deb
sudo systemctl enable --now docker
docker compose version
```

### 4. 构建并导出业务镜像

```bash
cd /path/to/repo/docs/docker
bash export-images.sh
# 产物在 offline-bundle/02-images/*.tar
```

导出后标签须为：`mysql:8.0`、`dataimport-backend:latest`、`dataimport-nginx:latest`。

### 5. 打包应用目录

把仓库中至少这些拷进 `offline-bundle/03-app/`（或整仓拷贝）：

- `docs/docker/`（含 `.env`、offline compose、nginx）  
- 仓库根目录的 `dataimport.sql`  

虚拟机 ↔ Windows ↔ U 盘 ↔ 正式机，按你方便的路径传 `offline-bundle` 即可。

---

## 二、备选：在 Windows Docker Desktop 上构建镜像

若不用虚拟机构建镜像，可在 Windows 上：

1. 安装 [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/)，WSL2 后端  
2. 在 `docs/docker` 执行 `.\export-images.ps1`  

**注意**：Docker 的 **deb 安装包仍建议在 Ubuntu 虚拟机里 `apt-get download`**，不要只在 Windows 下瞎下，依赖容易漏。

---

## 三、拷贝应用配置（无需在服务器上 build）

至少带上：

```text
docs/docker/                 # compose、nginx、.env
dataimport.sql               # 首次初始化库
```

在 Windows 上先写好 `.env`（密码等），一起拷过去；或到服务器再改。

离线启动请用 **不 build** 的编排文件：

```bash
cd /path/to/repo/docs/docker
cp .env.example .env   # 若还没有
# 编辑 .env

docker compose -f docker-compose.offline.yml up -d
```

`docker-compose.offline.yml` 只引用已 load 的镜像，**不会**访问外网。

---

## 四、正式无网 Ubuntu 上的加载与启动

```bash
# 1) 用 01-docker-engine 里的 deb 安装 Docker（见第一节）

# 2) 数据目录
sudo mkdir -p /home/mysqldata/{mysql,uploads,logs/nginx,backups}
sudo chown -R 999:999 /home/mysqldata/mysql
sudo chmod 750 /home/mysqldata/mysql

# 3) 加载镜像
cd /path/to/offline-bundle/02-images
sudo docker load -i mysql-8.0.tar
sudo docker load -i dataimport-backend.tar
sudo docker load -i dataimport-nginx.tar
sudo docker images   # 确认三个镜像都在

# 4) 启动（仓库 / 03-app 已拷到服务器）
cd /path/to/repo/docs/docker
sudo docker compose -f docker-compose.offline.yml up -d
sudo docker compose -f docker-compose.offline.yml ps
sudo docker compose -f docker-compose.offline.yml logs -f --tail=100
```

---

## 五、为什么不要在无网 Ubuntu 上 `docker compose build`

构建时会访问外网：

- 拉基础镜像：`python` / `node` / `nginx` / `mysql`
- `pip install`、`npm ci`、`apt-get` / `apk`

无网必失败。正确流程是：**有网虚拟机 build → save → 无网机 load → up（不 build）**。

以后改代码发版：在虚拟机重新 `bash export-images.sh`，只更新对应 tar，再到正式机 `docker load` 后 `compose up -d`。

---

## 六、体积与传输注意

- 三个 tar 合计常达 **数 GB**，用移动硬盘 / 共享文件夹 / 内网 scp 均可  
- 虚拟机、正式机架构须一致（常见 `amd64` / `x86_64`）  
- `dataimport.sql` 首次仅在空的 `/home/mysqldata/mysql` 时导入  

---

## 七、检查清单

| 步骤 | 有网 Ubuntu 虚拟机 | 无网正式 Ubuntu |
|------|-------------------|----------------|
| 下载 Docker deb | ✓ | `dpkg -i` 安装 |
| `export-images.sh`（build + save） | ✓ | ✗ 不要 build |
| `docker load` 三个镜像 | — | ✓ |
| 拷贝仓库 + `.env` | 打进 bundle | 放到固定目录 |
| `docker-compose.offline.yml up -d` | 可本机先试跑 | ✓ |

更细的日常运维见同目录 [README.md](./README.md)。
