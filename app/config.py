import secrets

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

WEAK_JWT_SECRETS = frozenset({"dev-secret", "change-me-in-production", "changeme", ""})
DEFAULT_INVITE_CODES = frozenset({"sailor2026", "sailor-admin"})


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    database_url: str = "sqlite:///./sailor.db"
    jwt_secret: str = "dev-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    upload_dir: str = "./uploads"
    upload_max_bytes: int = 15 * 1024 * 1024
    upload_allowed_extensions: str = ""
    public_base_url: str = ""
    content_dir: str = ""
    cors_origins: str = "http://localhost:8001"
    allowed_hosts: str = ""
    enable_docs: bool | None = None
    invite_code: str = "sailor2026"
    admin_invite_code: str = "sailor-admin"
    seed_admin_name: str = "管理员"
    seed_admin_password: str = "sailor-admin-2026"
    auth_rate_limit_per_minute: int = 30

    @property
    def is_production(self) -> bool:
        return self.app_env.strip().lower() == "production"

    @property
    def docs_enabled(self) -> bool:
        if self.enable_docs is not None:
            return self.enable_docs
        return not self.is_production

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def allowed_host_list(self) -> list[str]:
        return [h.strip() for h in self.allowed_hosts.split(",") if h.strip()]

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if not self.is_production:
            return self
        errors: list[str] = []
        if self.jwt_secret in WEAK_JWT_SECRETS or len(self.jwt_secret) < 32:
            errors.append("JWT_SECRET 在生产环境须至少 32 位且不能使用默认值")
        if self.invite_code in DEFAULT_INVITE_CODES:
            errors.append("INVITE_CODE 不能使用默认值，请设置独立邀请码")
        if self.admin_invite_code in DEFAULT_INVITE_CODES:
            errors.append("ADMIN_INVITE_CODE 不能使用默认值")
        if not self.cors_origin_list:
            errors.append("CORS_ORIGINS 不能为空")
        for origin in self.cors_origin_list:
            if "localhost" in origin or "127.0.0.1" in origin:
                errors.append(f"CORS_ORIGINS 生产环境不应包含本地地址: {origin}")
                break
        if not self.public_base_url.startswith("https://"):
            errors.append("PUBLIC_BASE_URL 生产环境应使用 https:// 前缀")
        if not self.allowed_host_list:
            errors.append("ALLOWED_HOSTS 生产环境必须设置（逗号分隔域名，如 api.example.com）")
        if errors:
            raise ValueError("生产配置校验失败: " + "; ".join(errors))
        return self


settings = Settings()


def generate_jwt_secret() -> str:
    return secrets.token_urlsafe(48)
