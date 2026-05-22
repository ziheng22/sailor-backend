# sailor-backend

sailor 工作室 **独立后端**（FastAPI + SQLite）。

前端仓库：`sailor-frontend`（另仓），通过 REST API 通信。

## 快速启动（固定习惯）

**本仓库 = 仅后端，端口 8000。** 不要用 `posthog.com` 或前端仓里的旧 `backend/`。

```powershell
cd sailor-backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

上级目录脚本：`..\scripts\start-backend.ps1`。双仓说明：[../REPOS.md](../REPOS.md)。

- 健康检查：<http://localhost:8000/health>
- 文档（开发）：<http://localhost:8000/docs>

## 内容（MDX → 数据库）

MDX 在 `contents/studio/`，见 [contents/README.md](./contents/README.md)。

```bash
python seed.py
python sync_slugs.py
```

## 本地与前端联调

| 服务 | 地址 |
|------|------|
| 本仓库 API | `http://localhost:8000` |
| 前端 | `http://localhost:8001`（`sailor-frontend`） |

`.env` 中 `CORS_ORIGINS=http://localhost:8001`。

## 生产部署（api 子域）

- 前端：`https://www.yoursite.com`
- API：`https://api.yoursite.com`（`ALLOWED_HOSTS`、`PUBLIC_BASE_URL`、`CORS_ORIGINS`）

详见 [DEPLOY.md](./DEPLOY.md)。

## 校园漫游（预留）

- **本仓库**：建筑 / 楼层 / POI / 导航 → SQLite（`campus_buildings`、`campus_pois`），`/api/campus/*`
- **前端仓库**：3D 模型与场景 JSON，用 `buildingId` 与 API 关联
