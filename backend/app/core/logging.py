from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from app.core.config import Settings


# All application loggers use the ``app.*`` hierarchy. This also captures
# existing component loggers such as ``app.materials`` without configuring the
# process-wide root logger or third-party libraries.
LOGGER_NAME = "app"


def get_app_logger(component: str | None = None) -> logging.Logger:
    name = LOGGER_NAME if not component else f"{LOGGER_NAME}.{component}"
    return logging.getLogger(name)


def _mark_handler(handler: logging.Handler) -> logging.Handler:
    setattr(handler, "_script_materials_handler", True)
    return handler


def configure_logging(config: Settings) -> logging.Logger:
    logger = get_app_logger()
    logger.setLevel(logging.DEBUG if config.debug and not config.is_production else logging.INFO)
    logger.propagate = False

    for handler in list(logger.handlers):
        if getattr(handler, "_script_materials_handler", False):
            logger.removeHandler(handler)
            handler.close()

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )

    if config.is_production:
        application_handler = _mark_handler(
            RotatingFileHandler(
                config.log_dir / "application.log",
                maxBytes=config.log_max_bytes,
                backupCount=config.log_backup_count,
                encoding="utf-8",
            )
        )
        application_handler.setLevel(logging.INFO)
        application_handler.setFormatter(formatter)
        logger.addHandler(application_handler)

        error_handler = _mark_handler(
            RotatingFileHandler(
                config.log_dir / "error.log",
                maxBytes=config.log_max_bytes,
                backupCount=config.log_backup_count,
                encoding="utf-8",
            )
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
    else:
        console_handler = _mark_handler(logging.StreamHandler())
        console_handler.setLevel(logger.level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    logger.info("application_starting environment=%s", config.app_env)
    return logger
