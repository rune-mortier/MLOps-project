import os
import sys

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../api"))

from database import Base, get_db
from main import app

TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def mock_model():
    m = MagicMock()
    m.predict.return_value = np.array([[5.0]])
    return m


@pytest.fixture
def mock_scaler():
    s = MagicMock()
    s.transform.side_effect = lambda x: x
    return s


@pytest.fixture
def client(db_session, mock_model, mock_scaler):
    app.dependency_overrides[get_db] = lambda: (yield db_session)

    with patch("main.init_db"):
        with patch("inference.load_model", return_value=(mock_model, mock_scaler)):
            with TestClient(app) as c:
                yield c

    app.dependency_overrides.clear()