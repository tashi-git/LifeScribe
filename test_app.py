"""
Test suite for the Flask Diary Application

This module contains comprehensive test cases for the diary app's API endpoints and basic web routes.
Tests cover user registration, login, diary entry management, and error handling scenarios.
Designed for GitHub CI integration using pytest framework.

Prerequisites:
- Flask app with MySQL database
- pytest installed
- Test database configured (consider using separate test DB for CI)

Fixtures:
- client: Flask test client for making requests
- db_setup: Database cleanup before/after tests
"""

import pytest
import json
from app import app, get_db_connection
import mysql.connector
from werkzeug.security import generate_password_hash
import datetime

@pytest.fixture
def client():
    
    """
    Pytest fixture to create a Flask test client.
    This fixture configures the app for testing mode and provides a test client
    that can be used to simulate HTTP requests to the application endpoints.
    """

    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def db_setup():
    """
    Pytest fixture for database setup and cleanup.

    This fixture ensures a clean test database state by removing any existing
    test users and entries before and after each test. In production CI,
    consider using a dedicated test database to avoid affecting production data.
    """
    # Setup test database - Note: In real CI, use a test database
    conn = get_db_connection()
    cur = conn.cursor()
    # Clean up any existing test data
    cur.execute("DELETE FROM entries WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'test%')")
    cur.execute("DELETE FROM users WHERE username LIKE 'test%'")
    conn.commit()
    cur.close()
    conn.close()
    yield
    # Cleanup after tests
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM entries WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'test%')")
    cur.execute("DELETE FROM users WHERE username LIKE 'test%'")
    conn.commit()
    cur.close()
    conn.close()

def test_api_register_success(client, db_setup):
    """
    Test successful user registration via API.

    This test verifies that a very something special new user can be registered successfully through
    the /api/register endpoint. It checks for proper response status and JSON structure.
    Corresponds to TC_REG_API_001 in testcase.txt.
    """
    data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass123'
    }
    response = client.post('/api/register', json=data)
    assert response.status_code == 200
    assert response.get_json() == {'status': 'success'}

def test_api_register_duplicate(client, db_setup):
    """
    Test registration failure due to duplicate username.

    This test ensures that attempting to register with an existing username
    returns an appropriate error message. It first registers a user, then
    attempts to register again with the same username.
    Corresponds to TC_REG_API_002 in testcase.txt.
    """
    # First register
    data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass123'
    }
    client.post('/api/register', json=data)

    # Try to register again
    data2 = {
        'username': 'testuser',
        'email': 'new@example.com',
        'password': 'testpass123'
    }
    response = client.post('/api/register', json=data2)
    assert response.status_code == 200
    assert response.get_json() == {'status': 'error', 'message': 'Username or email already exists!'}

def test_api_login_success(client, db_setup):
    """
    Test successful login via API.

    This test verifies that a registered user can log in successfully and
    receive a JWT token. It first registers a user, then attempts login.
    Corresponds to TC_LOGIN_API_001 in testcase.txt.
    """
    # Register first
    data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass123'
    }
    client.post('/api/register', json=data)

    # Login
    login_data = {
        'username': 'testuser',
        'password': 'testpass123'
    }
    response = client.post('/api/login', json=login_data)
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    assert 'token' in json_data
    assert 'user_id' in json_data

def test_api_login_invalid_credentials(client, db_setup):
    """
    Test login failure with invalid credentials.

    This test ensures that providing incorrect login credentials results
    in an appropriate error response. It registers a user first, then
    attempts login with wrong password.
    Corresponds to TC_LOGIN_API_002 in testcase.txt.
    """
    # Register first
    data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass123'
    }
    client.post('/api/register', json=data)

    # Login with wrong password
    login_data = {
        'username': 'testuser',
        'password': 'wrongpass'
    }
    response = client.post('/api/login', json=login_data)
    assert response.status_code == 200
    assert response.get_json() == {'status': 'error', 'message': 'Invalid credentials!'}

def test_api_add_entry_success(client, db_setup):
    """
    Test adding a new diary entry via API.

    This test verifies that authenticated users can add diary entries.
    It registers a user, logs in to get a token, then adds an entry.
    Corresponds to TC_ENTRY_API_001 in testcase.txt.
    """
    # Register and login
    data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass123'
    }
    client.post('/api/register', json=data)

    login_data = {
        'username': 'testuser',
        'password': 'testpass123'
    }
    response = client.post('/api/login', json=login_data)
    token = response.get_json()['token']

    # Add entry
    entry_data = {'content': 'This is a test diary entry'}
    headers = {'Authorization': f'Bearer {token}'}
    response = client.post('/api/entry', json=entry_data, headers=headers)
    assert response.status_code == 200
    assert response.get_json() == {'status': 'success'}

def test_api_add_entry_unauthorized(client, db_setup):
    """
    Test adding entry without valid token.

    This test ensures that attempting to add a diary entry without
    proper authentication returns an unauthorized error.
    Corresponds to TC_ENTRY_API_002 in testcase.txt.
    """
    entry_data = {'content': 'This is a test diary entry'}
    response = client.post('/api/entry', json=entry_data)
    assert response.status_code == 401
    assert response.get_json() == {'message': 'Token is missing!'}

def test_api_get_entries_success(client, db_setup):
    """
    Test retrieving user's diary entries via API.

    This test verifies that authenticated users can retrieve their
    diary entries. It registers a user, logs in, adds an entry, then retrieves entries.
    Corresponds to TC_GET_ENTRIES_API_001 in testcase.txt.
    """
    # Register, login, add entry
    data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass123'
    }
    client.post('/api/register', json=data)

    login_data = {
        'username': 'testuser',
        'password': 'testpass123'
    }
    response = client.post('/api/login', json=login_data)
    token = response.get_json()['token']

    entry_data = {'content': 'This is a test diary entry'}
    headers = {'Authorization': f'Bearer {token}'}
    client.post('/api/entry', json=entry_data, headers=headers)

    # Get entries
    response = client.get('/api/entries', headers=headers)
    assert response.status_code == 200
    entries = response.get_json()
    assert isinstance(entries, list)
    assert len(entries) >= 1
    assert entries[0]['content'] == 'This is a test diary entry'

def test_api_get_entries_unauthorized(client, db_setup):
    """
    Test retrieving entries without token.

    This test ensures that attempting to retrieve diary entries without
    authentication returns an unauthorized error.
    Corresponds to TC_GET_ENTRIES_API_002 in testcase.txt.
    """
    response = client.get('/api/entries')
    assert response.status_code == 401
    assert response.get_json() == {'message': 'Token is missing!'}

def test_index_redirect_not_logged_in(client):
    """
    Test index route behavior when not logged in.

    This test verifies that accessing the root route without being logged in
    redirects to the login page.
    Corresponds to TC_INDEX_001 in testcase.txt.
    """
    response = client.get('/')
    assert response.status_code == 302  # Redirect
    assert '/login' in response.headers['Location']

def test_protected_route_without_login(client):
    """
    Test accessing protected route without login.

    This test ensures that attempting to access the diary page without
    being logged in redirects to the login page.
    Corresponds to TC_PROTECTED_001 in testcase.txt.
    """
    response = client.get('/diary')
    assert response.status_code == 302  # Redirect
    assert '/login' in response.headers['Location']

# Note: Web route tests (login/register forms) would require selenium or similar for full testing
# These are basic API tests. For comprehensive CI, consider adding more integration tests.

if __name__ == '__main__':
    pytest.main()
