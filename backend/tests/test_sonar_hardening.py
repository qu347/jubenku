import subprocess
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.services.genre_metric_service import GenreMetricService


def test_development_settings_default_to_same_origin_requests() -> None:
    assert Settings().cors_origin_list == []


@pytest.mark.parametrize("origin", ["http://example.com", "*"])
def test_production_settings_reject_insecure_external_cors_origins(origin: str) -> None:
    with pytest.raises(ValueError, match="CORS"):
        Settings(app_env="production", cors_allowed_origins=origin)


def test_validation_reason_handles_malformed_error_type() -> None:
    assert GenreMetricService._validation_reason(
        {"type": {"unexpected": "mapping"}, "msg": "输入值不合法"}
    ) == "输入值不合法"


def test_alembic_does_not_evaluate_logging_handler_arguments(tmp_path: Path) -> None:
    backend_root = Path(__file__).resolve().parents[1]
    marker = Path(tempfile.gettempdir()) / f"jubenku-alembic-{uuid4().hex}"
    config_file = tmp_path / "alembic.ini"
    handler_args = (
        f"(__import__('pathlib').Path({marker.as_posix()!r}).write_text('executed') "
        "and __import__('sys').stderr,)"
    )
    config_file.write_text(
        f"""[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = sqlite://

[loggers]
keys = root

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[handler_console]
class = StreamHandler
args = {handler_args}
level = NOTSET
formatter = generic

[formatter_generic]
format = %%(levelname)s [%%(name)s] %%(message)s
""",
        encoding="utf-8",
    )

    try:
        completed = subprocess.run(
            [sys.executable, "-m", "alembic", "-c", str(config_file), "current"],
            cwd=backend_root,
            capture_output=True,
            text=True,
            check=False,
        )

        assert completed.returncode == 0, completed.stderr
        assert not marker.exists()
    finally:
        marker.unlink(missing_ok=True)
