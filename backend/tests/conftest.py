import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.db.session import engine, get_db
from app.main import app


@pytest.fixture()
def db_session():
    """A session bound to a connection-level transaction that's always rolled
    back at teardown — even if the endpoint under test calls db.commit()."""
    connection = engine.connect()
    transaction = connection.begin()
    TestSessionLocal = sessionmaker(bind=connection, join_transaction_mode="create_savepoint")
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
