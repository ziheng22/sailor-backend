# AGENTS.md — sailor-backend

## 固定开发习惯（必须遵守）

- **只在本仓库改后端代码**，路径：`sailor-backend/`
- 启动：`uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
- 前端在**另一仓库** `sailor-frontend/`，端口 **8001**
- **不要使用** 已废弃目录 `posthog.com` 或嵌在前端里的旧 `backend/`

MDX 内容源：`contents/studio/` → `python seed.py` 导入 SQLite。

## 命令

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
python seed.py
python sync_slugs.py
```

## 目录

```text
app/routers/    # API
app/models/     # 数据模型（含 campus_* 预留）
contents/       # MDX 种子
uploads/        # 上传文件
```

## 协作说明

- 与 `sailor-frontend` 为独立 Git 仓库
- 总览：`../REPOS.md`、`../scripts/start-backend.ps1`
