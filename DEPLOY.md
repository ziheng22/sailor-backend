# 生产部署清单

上线前逐项确认，避免默认密钥与开放文档导致的安全问题。

## 1. 环境变量（必填）

复制 `.env.production.example` 为 `.env`，并替换所有 `REPLACE_*` 占位：

| 变量 | 要求 |
|------|------|
| `APP_ENV` | 必须为 `production`（触发启动校验） |
| `JWT_SECRET` | ≥32 字符，`python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `INVITE_CODE` / `ADMIN_INVITE_CODE` | 不得使用 `sailor2026` / `sailor-admin` |
| `CORS_ORIGINS` | 前端 HTTPS 域名，禁止 localhost |
| `PUBLIC_BASE_URL` | API 对外地址，须 `https://` |
| `ALLOWED_HOSTS` | 与反代 Host 一致，如 `api.yoursite.com` |
| `ENABLE_DOCS` | 建议 `false`（默认生产关闭 `/docs`） |

## 2. 运行方式

### Docker（推荐）

```bash
cp .env.production.example .env
# 编辑 .env 后
docker compose -f docker-compose.prod.yml up -d --build
```

数据卷 `sailor_data` 持久化 `/data`（SQLite + uploads）。

### 裸机 / systemd

```bash
pip install -r requirements.txt
gunicorn app.main:app -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000 -w 2
```

仅监听本机，由 Nginx/Caddy 反代并终止 TLS。

## 3. 反向代理

- 对外仅暴露 **HTTPS**
- 将 `Host` 转发到后端（与 `ALLOWED_HOSTS` 一致）
- 静态上传路径 `/uploads` 可由 CDN 或同域反代
- 设置合理 `client_max_body_size`（≥ `UPLOAD_MAX_BYTES`）

## 4. 安全基线（已实现）

- 生产配置启动时校验密钥、CORS、TrustedHost
- 安全响应头（`X-Frame-Options`、`HSTS` 等）
- 认证接口按 IP 限流（`AUTH_RATE_LIMIT_PER_MINUTE`）
- 未捕获异常在生产环境不返回堆栈
- SQLite WAL + 外键
- 容器内非 root 用户运行

## 5. 上线后验证

```bash
curl -s https://api.yoursite.com/health
# {"status":"ok"}

# 生产应 404
curl -s -o /dev/null -w "%{http_code}" https://api.yoursite.com/docs
```

前端构建时设置 `VITE_API_BASE_URL=https://api.yoursite.com`。

## 6. 禁止事项

- 勿将 `.env` 提交到 Git
- 勿在生产开启默认邀请码或 `JWT_SECRET=dev-secret`
- 勿对公网直接暴露未加 TLS 的 8000 端口（除非仅内网）

## 7. 备份

定期备份 `DATABASE_URL` 指向的库文件与 `UPLOAD_DIR` 目录。
