#!/bin/sh
set -eu

# 由 Compose 环境变量生成 set.config，避免镜像内写死密码
CONFIG_FILE="${DATAIMPORT_CONFIG_FILE:-/app/set.config}"

cat > "$CONFIG_FILE" <<EOF
# 由 docker-entrypoint.sh 自动生成，请勿手改容器内文件；改 .env 后重建/重启即可
[DATABASE]
DB_HOST = ${DB_HOST:-mysql}
DB_PORT = ${DB_PORT:-3306}
DB_USER = ${DB_USER:-dataimport}
DB_PASSWORD = ${DB_PASSWORD}
DB_NAME = ${DB_NAME:-dataimport}
DB_CHARSET = ${DB_CHARSET:-utf8mb4}

[SECURITY]
SECRET_KEY = ${SECRET_KEY:-key031125}
JWT_SECRET_KEY = ${JWT_SECRET_KEY:-jwt_key031125}
JWT_ACCESS_TOKEN_EXPIRES = ${JWT_ACCESS_TOKEN_EXPIRES:-3600}

[UPLOAD]
UPLOAD_FOLDER = ${UPLOAD_FOLDER:-uploads}
MAX_CONTENT_LENGTH = 104857600
ALLOWED_EXTENSIONS = pdf,doc,docx,jpg,jpeg,png,txt,xlsx,xls,ppt,pptx,zip,rar
UPLOAD_PATH = uploads
FILE_NAME_LENGTH = 255
UPLOAD_TIMEOUT = 300

[APPLICATION]
DEBUG = off
HOST = 0.0.0.0
PORT = 5000
THREADED = True

[LOGGING]
LOG_LEVEL = INFO
LOG_FILE = logs/app.log
LOG_MAX_SIZE = 10485760
LOG_BACKUP_COUNT = 5
EOF

mkdir -p /app/uploads /app/logs

if [ "$1" = "gunicorn" ]; then
  shift
  exec gunicorn \
    --bind "${GUNICORN_BIND:-0.0.0.0:5000}" \
    --workers "${GUNICORN_WORKERS:-4}" \
    --timeout "${GUNICORN_TIMEOUT:-300}" \
    --access-logfile - \
    --error-logfile - \
    "app:app" \
    "$@"
fi

exec "$@"
