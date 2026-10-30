import os

os.environ["LLM_PROVIDER"] = "mock"  # tests never call a real LLM

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c
