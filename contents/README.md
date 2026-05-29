# 内容源（MDX）

工作室原始内容放在 `contents/studio/`，**仅用于后端** `seed.py` 导入 SQLite。

前端不再打包 MDX，运行时一律请求 API。

## 维护流程

```bash
# 编辑 *.mdx 后
python seed.py          # 导入/更新数据库
python sync_slugs.py    # 对齐 slug 与文件名
```

## 目录

- `index.mdx`、`join.mdx`、`contact.mdx`：静态页
- `current-members/`、`alumni/`、`projects/`、`notes/`：各栏目
