import pytest


class TestAuth:
    """Tests for authentication endpoints."""

    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post('/api/auth/register', json={
            'email': 'newuser@example.com',
            'password': 'Password123',
            'display_name': 'New User'
        })

        assert response.status_code == 201
        data = response.get_json()
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert data['user']['email'] == 'newuser@example.com'

    def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        response = client.post('/api/auth/register', json={
            'email': 'invalid-email',
            'password': 'Password123',
            'display_name': 'New User'
        })

        assert response.status_code == 400

    def test_register_weak_password(self, client):
        """Test registration with weak password."""
        response = client.post('/api/auth/register', json={
            'email': 'user@example.com',
            'password': 'weak',
            'display_name': 'New User'
        })

        assert response.status_code == 400

    def test_register_duplicate_email(self, client, db_session):
        """Test registration with duplicate email."""
        # First registration
        client.post('/api/auth/register', json={
            'email': 'duplicate@example.com',
            'password': 'Password123',
            'display_name': 'First User'
        })

        # Second registration with same email
        response = client.post('/api/auth/register', json={
            'email': 'duplicate@example.com',
            'password': 'Password123',
            'display_name': 'Second User'
        })

        assert response.status_code == 409

    def test_login_success(self, client, db_session):
        """Test successful login."""
        # First register
        client.post('/api/auth/register', json={
            'email': 'loginuser@example.com',
            'password': 'Password123',
            'display_name': 'Login User'
        })

        # Then login
        response = client.post('/api/auth/login', json={
            'email': 'loginuser@example.com',
            'password': 'Password123'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
        assert 'refresh_token' in data

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post('/api/auth/login', json={
            'email': 'nonexistent@example.com',
            'password': 'WrongPassword123'
        })

        assert response.status_code == 401

    def test_get_current_user(self, client, auth_headers):
        """Test getting current user profile."""
        response = client.get('/api/auth/me', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'email' in data

    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without authentication."""
        response = client.get('/api/auth/me')

        assert response.status_code == 401
