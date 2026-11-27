def test_signup_success(client):
    response = client.post(
        "/auth/signup",
        json={
            "email": "test@example.com",
            "password": "securepassword123",
            "full_name": "Test User",
            "role":'zarp'
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert "id" in data
    assert "hashed_password" not in data  # Ensure password hash isn't leaked

def test_signup_duplicate_email(client):
    payload = {
        "email": "duplicate@example.com",
        "password": "securepassword123"
    }
    # First signup
    client.post("/auth/signup", json=payload)
    
    # Second signup with same email
    response = client.post("/auth/signup", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

def test_login_success(client):
    client.post(
        "/auth/signup",
        json={
            "email": "login@example.com",
            "password": "mypassword123"
        }
    )
    
    response = client.post(
        "/auth/login",
        json={
            "email": "login@example.com",
            "password": "mypassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client):
    client.post(
        "/auth/signup",
        json={
            "email": "login@example.com",
            "password": "mypassword123"
        }
    )
    
    response = client.post(
        "/auth/login",
        json={
            "email": "login@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

def test_read_users_me(client):
    # Register and login to get token
    client.post(
        "/auth/signup",
        json={
            "email": "me@example.com",
            "password": "password123",
            "full_name": "Me User"
        }
    )
    login_res = client.post(
        "/auth/login",
        json={
            "email": "me@example.com",
            "password": "password123"
        }
    )
    token = login_res.json()["access_token"]

    # Access protected route
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert data["full_name"] == "Me User"

def test_read_users_me_unauthorized(client):
    response = client.get("/auth/me")
    assert response.status_code == 401