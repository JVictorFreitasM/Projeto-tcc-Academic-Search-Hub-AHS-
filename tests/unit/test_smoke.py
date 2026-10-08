import pytest


@pytest.mark.unit
def test_smoke() -> None:
    """Confirma que o ambiente de testes funciona."""
    assert 1 + 1 == 2
