from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models.article import Article
from app.models.member import Member
from app.models.page import Page
from app.models.user import User
from app.passwords import hash_password

TEST_PASSWORD = "test-pass-123"

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()
db.add(Member(status="current", name="张三", role="开发", grade="2024级"))
db.add(
    User(
        name="张三",
        grade="2024级",
        role="member",
        member_id=1,
        password_hash=hash_password(TEST_PASSWORD),
    )
)
db.add(
    User(
        name="管理员",
        grade="管理员",
        role="admin",
        member_id=None,
        password_hash=hash_password(TEST_PASSWORD),
    )
)
db.add(Article(title="测试日志", body="hello", member_names="[]"))
db.add(Page(slug="index", title="启航手册", body="# old"))
db.commit()
db.close()

client = TestClient(app)

r = client.post(
    "/api/auth/login",
    json={"invite_code": "sailor2026", "name": "张三", "password": TEST_PASSWORD},
)
assert r.status_code == 200, r.text
member_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

assert (
    client.put("/api/member/profile", headers=member_headers, json={"intro": "新简介"}).status_code
    == 200
)
assert (
    client.post(
        "/api/member/articles",
        headers=member_headers,
        json={"title": "新日志", "body": "内容", "member_names": '["张三"]'},
    ).status_code
    == 201
)
article_id = client.post(
    "/api/member/articles",
    headers=member_headers,
    json={"title": "x", "body": "y"},
).json()["id"]
revs = client.get(f"/api/articles/{article_id}/revisions")
assert revs.status_code == 200 and len(revs.json()) >= 1
assert (
    client.post(
        "/api/admin/members",
        headers=member_headers,
        json={"name": "李四", "status": "current"},
    ).status_code
    == 403
)

r = client.post(
    "/api/auth/login",
    json={"invite_code": "sailor-admin", "name": "管理员", "password": TEST_PASSWORD},
)
assert r.status_code == 200, r.text
admin_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

assert (
    client.post(
        "/api/admin/members",
        headers=admin_headers,
        json={"name": "李四", "status": "current"},
    ).status_code
    == 201
)
assert (
    client.put(
        "/api/admin/pages/index",
        headers=admin_headers,
        json={"title": "新手册", "body": "# hi"},
    ).status_code
    == 200
)
assert (
    client.put("/api/admin/pages/join", headers=admin_headers, json={"body": "join"}).status_code
    == 404
)

print("permission smoke test passed")
