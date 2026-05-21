import logging
import sys

from .config import settings

logger = logging.getLogger("sailor")


def run_startup_checks() -> None:
    if settings.is_production:
        logger.info("Running in production mode")
        if settings.docs_enabled:
            logger.warning("API docs are enabled in production (ENABLE_DOCS=true)")
    else:
        if settings.jwt_secret == "dev-secret":
            logger.warning("Using default JWT_SECRET — set a strong secret before production")


def configure_logging() -> None:
    level = logging.INFO if settings.is_production else logging.DEBUG
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        stream=sys.stdout,
    )
