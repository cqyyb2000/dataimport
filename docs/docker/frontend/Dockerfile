# 前端多阶段构建：Node 编译 → Nginx 托管静态资源
# 构建上下文：仓库根目录

FROM node:20-alpine AS builder

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ .

ARG VUE_APP_API_BASE_URL=/api
ENV VUE_APP_API_BASE_URL=$VUE_APP_API_BASE_URL

RUN npm run build

FROM nginx:1.27-alpine

ENV TZ=Asia/Shanghai
RUN apk add --no-cache tzdata \
    && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo Asia/Shanghai > /etc/timezone

COPY --from=builder /app/dist /usr/share/nginx/html
COPY docs/docker/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY docs/docker/nginx/nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
