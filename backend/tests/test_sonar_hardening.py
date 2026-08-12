import pytest

from app.core.config import Settings
from app.services.genre_metric_service import GenreMetricService


@pytest.mark.parametrize("origin", ["http://example.com", "*"])
def test_production_settings_reject_insecure_external_cors_origins(origin: str) -> None:
    with pytest.raises(ValueError, match="CORS"):
        Settings(app_env="production", cors_allowed_origins=origin)


def test_validation_reason_handles_malformed_error_type() -> None:
    assert GenreMetricService._validation_reason(
        {"type": {"unexpected": "mapping"}, "msg": "输入值不合法"}
    ) == "输入值不合法"
