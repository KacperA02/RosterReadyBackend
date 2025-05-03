# Imported necessary modules for testing, including pytest, TestClient, and other dependencies
# Imported pytest for running the tests.
import pytest
# Imported TestClient to simulate HTTP requests to the FastAPI app for testing. This is used to test endpoints without needing to run the server.
from fastapi.testclient import TestClient
# Imported the main FastAPI app to be able to interact with it during testing.
from app.main import app 
# Imported patch to mock functions during the test. This allows to replace actual functions with mock objects.
# MagicMock to create mock objects for testing. This allows for testing without actually seeding the db before testing
from unittest.mock import patch, MagicMock
# Status to compare the status of each for the results.
from fastapi import status
# Created an instance of TestClient for testing the FastAPI app
client = TestClient(app)

# Created a test function to simulate a successful login request
# Mocked the get_user_by_email function
@patch("app.routes.auth_route.get_user_by_email")
# Mocked the verify_password function  
@patch("app.routes.auth_route.verify_password")
def test_login_success(mock_verify_password, mock_get_user_by_email):
    
    mock_user = MagicMock()
    mock_user.email = "testuser@example.com"
    mock_user.password = "testpassword123"
    
    # Created a mock role object with the name 'Customer'
    mock_role = MagicMock()
    mock_role.name = "Customer"
    
    # Assigned the mock role to the user object
    mock_user.roles = [mock_role]
    mock_user.id = 1
    mock_user.team_id = 1

    # Configured the mock to return this mock user object when the get_user_by_email function is called
    mock_get_user_by_email.return_value = mock_user
    
    # Mocked the password verification to always return True, as this function has access to which status to display
    mock_verify_password.return_value = True
    
    # Prepared the login data with email and password for the test
    login_data = {
        "email": "testuser@example.com",
        "password": "testpassword123"
    }

    # Simulated a POST request to the login endpoint with the login data
    response = client.post("/auth/login", json=login_data)

    # Checked the response status code and token information to ensure the login was successful
    # The assert statement in Python is used to test if a condition is true.
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

# Created a test function to simulate a failed login due to incorrect password
@patch("app.routes.auth_route.get_user_by_email")  # Mocked the get_user_by_email function
@patch("app.routes.auth_route.verify_password")  # Mocked the verify_password function
def test_login_fail_wrong_password(mock_verify_password, mock_get_user_by_email):
    # Mocked the user object with similar attributes as before
    mock_user = MagicMock()
    mock_user.email = "testuser@example.com"
    mock_user.password = "testpassword123"
    
    # Created a mock role object with the name 'Customer'
    mock_role = MagicMock()
    mock_role.name = "Customer"
    
    # Assigned the mock role to the user object
    mock_user.roles = [mock_role]
    mock_user.id = 1
    mock_user.team_id = 1

    # Configured the mock to return this mock user object when the get_user_by_email function is called
    mock_get_user_by_email.return_value = mock_user

    # Mocked the password verification to return False, as this function has access to which status to display
    mock_verify_password.return_value = False

    # Prepared the login data with an incorrect password for the test
    login_data = {
        "email": "testuser@example.com",
        "password": "wrongpassword"
    }

    # Simulated a POST request to the login endpoint with the login data
    response = client.post("/auth/login", json=login_data)

    # Checked the response status code and error message to ensure the failed login was correctly handled
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Incorrect email or password"
