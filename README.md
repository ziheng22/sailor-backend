# 后端 API（`backend/`）

sailor 工作室内容 API（FastAPI + SQLite）。

在仓库中的位置：**`sailor-studio/backend/`**（与前端 `src/`、`contents/` 同级）。  
若你仍看到独立的 `sailor-backend` 文件夹，那是同一套代码的联接/副本，以仓库内的 `backend/` 为准。

## 快速启动

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

或在仓库根目录：`pnpm run api`

健康检查：<http://localhost:8000/health>  
接口文档：<http://localhost:8000/docs>

## 环境变量

见 `.env.example`。常用项：

| 变量 | 说明 |
|------|------|
| `JWT_SECRET` | 生产环境务必修改 |
| `INVITE_CODE` | 成员注册/登录邀请码 |
| `ADMIN_INVITE_CODE` | 管理员邀请码 |
| `CORS_ORIGINS` | 前端地址，默认 `http://localhost:8001` |
| `CONTENT_DIR` | seed / sync_slugs 用的 MDX 目录 |
| `PUBLIC_BASE_URL` | 上传文件对外 URL 前缀（如 `http://localhost:8000`） |
| `UPLOAD_MAX_BYTES` | 单文件大小上限（默认 15MB） |
| `UPLOAD_ALLOWED_EXTENSIONS` | 允许的扩展名，逗号分隔；留空用内置白名单 |

## 初始化数据

```bash
cd backend
python seed.py
python sync_slugs.py
```

默认从 `../contents/studio` 读取 MDX（无需再写绝对路径）。

`sync_slugs.py` 将数据库中的 `slug` 与 MDX 文件名（`*.mdx` 的 stem，如 `liu-jiapeng`）对齐，便于前端使用语义化 URL 而非纯数字 id。

## 权限摘要

| 能力 | 成员 | 管理员 |
|------|------|--------|
| 航海日志编辑 | ✅（全员，保留修订记录） | ✅ |
| 日志截止时间 `completed_at`（仅登录可见） | ❌ | ✅ |
| 日志关联成员名 `member_names` | ✅ | ✅ |
| 积分榜查看 | ✅（需登录，可看全员排名与流水） | ✅ |
| 积分下发 | ❌ | ✅ |
| 校园漫游 `/api/campus/*` | 公开占位，待同伴对接 | |

## 主要接口

- 公开：`/api/members`、`/api/articles`、`/api/projects`、`/api/pages/{slug}`
- 按 slug：`/api/articles/by-slug/{slug}` 等
- 登录：`/api/auth/login`、`/api/auth/register`
- 成员：`/api/member/profile`、`/api/member/articles`
- 积分（需登录）：`GET /api/points/leaderboard`
- 管理员积分：`POST /api/admin/points/award`
- 校园预留：`GET /api/campus`、`GET /api/campus/buildings`
- 管理员上传：`POST /api/admin/uploads`（multipart）、`GET` 列表、`DELETE /{id}`

## 生产部署

详见 **[DEPLOY.md](./DEPLOY.md)**。

要点：

- `APP_ENV=production` 时启动会校验 `JWT_SECRET`、邀请码、`CORS_ORIGINS`、`PUBLIC_BASE_URL`、`ALLOWED_HOSTS`
- 默认关闭 `/docs`；可用 `ENABLE_DOCS=true` 临时开启
- Docker：`docker compose -f docker-compose.prod.yml up -d --build`
- 进程建议用 gunicorn + uvicorn worker（见 `Dockerfile`）

| 变量 | 开发默认 | 生产 |
|------|----------|------|
| `APP_ENV` | development | production |
| `ALLOWED_HOSTS` | 空（不启用 TrustedHost） | 必填 |
| `ENABLE_DOCS` | 自动开启 | 自动关闭 |

## 迁移

启动时自动执行 `app/migrate.py`，为旧库补列（slug、积分、日志字段等）。
