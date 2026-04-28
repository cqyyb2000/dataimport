# -*- coding: utf-8 -*-
"""
使用 Waitress 启动 Flask（适合 Windows 生产部署）。

用法（在 backend 目录、已激活虚拟环境）:
  python run_waitress.py

可选环境变量:
  WAITRESS_HOST   默认取 set.config [APPLICATION] HOST，再否则 0.0.0.0
  WAITRESS_PORT   默认取 set.config [APPLICATION] PORT，再否则 5501
  WAITRESS_THREADS 工作线程数，默认 4

可配合 NSSM 等注册为 Windows 服务。
set.config 与 .env 均相对 backend 目录解析（不依赖服务进程的当前工作目录）。
"""
from __future__ import annotations

import importlib
import os

from app import app, setup_logging
from config_reader import config_reader


def main() -> None:
    setup_logging()

    host = os.environ.get("WAITRESS_HOST")
    port_str = os.environ.get("WAITRESS_PORT")
    threads = int(os.environ.get("WAITRESS_THREADS", "4"))

    if config_reader:
        try:
            cfg = config_reader.get_application_config()
            if not host:
                host = cfg.get("host") or "0.0.0.0"
            if not port_str:
                port_str = str(cfg.get("port") or 5501)
        except Exception:
            if not host:
                host = "0.0.0.0"
            if not port_str:
                port_str = "5501"
    else:
        if not host:
            host = "0.0.0.0"
        if not port_str:
            port_str = "5501"

    port = int(port_str)

    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI")
    if db_uri:
        print(f"数据库连接串: {db_uri}")

    try:
        _waitress = importlib.import_module("waitress")
        serve = _waitress.serve
    except ImportError as e:
        raise SystemExit(
            "未安装 waitress，请执行: pip install waitress"
        ) from e

    print(f"Waitress 监听 http://{host}:{port} ，线程数 {threads}")
    serve(app, host=host, port=port, threads=threads)


if __name__ == "__main__":
    main()
