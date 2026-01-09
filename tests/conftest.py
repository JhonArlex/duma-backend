import pytest
from app import create_app
from app.extensions import db
from app.config import TestingConfig


@pytest.fixture(scope='session')
def app():
    """Create application for the tests."""
    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """Create a database session for tests."""
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()

        yield db.session

        transaction.rollback()
        connection.close()


@pytest.fixture
def auth_headers(client):
    """Create authentication headers for tests."""
    # Register a test user
    response = client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'TestPassword123',
        'display_name': 'Test User'
    })

    if response.status_code == 201:
        data = response.get_json()
        return {'Authorization': f'Bearer {data["access_token"]}'}

    # If user already exists, login
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'TestPassword123'
    })
    data = response.get_json()
    return {'Authorization': f'Bearer {data["access_token"]}'}
