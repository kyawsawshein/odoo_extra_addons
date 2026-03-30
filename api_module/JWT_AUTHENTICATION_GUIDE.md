# JWT Authentication Guide for Odoo API Module

This guide explains how to set up and use JWT authentication between Odoo and the external odoo_api service.

## Overview

The JWT authentication system allows users to:
- Authenticate using JWT tokens from odoo_api
- Login to Odoo using odoo_api credentials
- Maintain secure session-based authentication
- Access Odoo data through JWT-verified requests

## Configuration

### 1. Enable JWT Authentication in API Configuration

1. Go to **API Configurations** in Odoo
2. Create or edit an API configuration
3. In the **JWT Authentication** section:
   - Check **Enable JWT Authentication**
   - Set **JWT Secret Key** (must match the secret in odoo_api)
   - Select **JWT Algorithm** (default: HS256)

### 2. odoo_api Configuration

Ensure your odoo_api service has the same JWT secret key configured in the `settings.SECRET_KEY` variable.

## API Endpoints

### JWT Token Generation (for odoo_api)
**POST** `/api/v1/auth/jwt/generate-token`

Generate JWT token for authenticated Odoo user. This endpoint is called by odoo_api when users authenticate via `/odoo-login`.

**Request Body:**
```json
{
  "username": "your-odoo-username",
  "password": "your-odoo-password"
}
```

**Response:**
```json
{
  "success": true,
  "message": "JWT token generated successfully",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user_id": 2,
    "username": "admin",
    "name": "Administrator"
  }
}
```

### JWT Login
**POST** `/api/v1/auth/jwt/login`

Authenticate using JWT token or username/password.

**Request Body Options:**
```json
{
  "jwt_token": "your-jwt-token-from-odoo-api"
}
```
OR
```json
{
  "username": "your-username",
  "password": "your-password"
}
```

**Response:**
```json
{
  "success": true,
  "message": "JWT authentication successful",
  "data": {
    "user_id": 2,
    "username": "admin",
    "name": "Administrator",
    "jwt_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "session_id": "session-id-here"
  }
}
```

### Verify JWT Token
**POST** `/api/v1/auth/jwt/verify`

Verify a JWT token and get user information.

**Request Body:**
```json
{
  "jwt_token": "your-jwt-token"
}
```

**Response:**
```json
{
  "success": true,
  "message": "JWT token is valid",
  "data": {
    "user_id": 2,
    "username": "admin",
    "name": "Administrator",
    "jwt_payload": {
      "sub": "admin",
      "user_id": 2,
      "exp": 1730625600
    }
  }
}
```

### Get Current User
**GET** `/api/v1/auth/jwt/me`

Get information about the currently authenticated user.

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": 2,
    "username": "admin",
    "name": "Administrator",
    "email": "admin@example.com",
    "company_id": 1,
    "company_name": "Your Company",
    "groups": ["Administration", "User"]
  }
}
```

### Logout
**POST** `/api/v1/auth/jwt/logout`

Logout the current user.

**Response:**
```json
{
  "success": true,
  "message": "Logout successful"
}
```

## Usage Examples

### 1. Login with Username/Password
```python
import requests

# Login to get JWT token
response = requests.post(
    "http://your-odoo-url/api/v1/auth/jwt/login",
    json={
        "username": "admin",
        "password": "admin"
    }
)

if response.json()["success"]:
    session_id = response.json()["data"]["session_id"]
    jwt_token = response.json()["data"]["jwt_token"]
    
    # Use session_id for subsequent requests
    headers = {"Cookie": f"session_id={session_id}"}
```

### 2. Login with Existing JWT Token
```python
import requests

# Use existing JWT token from odoo_api
response = requests.post(
    "http://your-odoo-url/api/v1/auth/jwt/login",
    json={
        "jwt_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
)
```

### 3. Verify Token
```python
import requests

# Verify JWT token
response = requests.post(
    "http://your-odoo-url/api/v1/auth/jwt/verify",
    json={
        "jwt_token": "your-jwt-token"
    }
)

if response.json()["success"]:
    print("Token is valid")
    user_info = response.json()["data"]
```

## Integration Flow with odoo_api

### JWT Token Generation Flow

1. **User authenticates with odoo_api** via `/api/v1/auth/token`
2. **odoo_api calls Odoo authentication** via `/odoo-login` endpoint
3. **Odoo module generates JWT token** via `/api/v1/auth/jwt/generate-token`
4. **JWT token returned to odoo_api** with user information
5. **odoo_api returns JWT token** to the client application

### Sequence Diagram

```
Client App -> odoo_api: POST /api/v1/auth/token
odoo_api -> Odoo: POST /odoo-login (with Odoo credentials)
Odoo -> Odoo Module: POST /api/v1/auth/jwt/generate-token
Odoo Module -> odoo_api: Return JWT token + user data
odoo_api -> Client App: Return JWT token
```

### Example Integration

When a user logs into odoo_api with Odoo credentials:

1. odoo_api validates the user's credentials
2. odoo_api calls the Odoo module to generate a JWT token
3. The Odoo module authenticates the user and generates a JWT token
4. The JWT token is returned to odoo_api with user information
5. odoo_api returns the JWT token to the client

## Integration with Existing API Routes

The JWT authentication system works alongside the existing API key and Basic Auth authentication methods. When JWT authentication is enabled:

1. Users can authenticate using JWT tokens
2. The system automatically creates Odoo users from JWT payloads
3. Session-based authentication is maintained
4. All existing API routes remain accessible

## Security Considerations

1. **JWT Secret Key**: Keep the JWT secret key secure and never commit it to version control
2. **Token Expiration**: JWT tokens have expiration times for security
3. **User Creation**: The system can create Odoo users automatically from JWT payloads
4. **Session Management**: Proper session cleanup on logout

## Troubleshooting

### Common Issues

1. **"No active JWT configuration found"**
   - Ensure JWT authentication is enabled in API configuration
   - Check that the configuration is active

2. **"JWT secret not configured"**
   - Set the JWT secret key in the API configuration

3. **"Invalid or expired JWT token"**
   - Check token expiration
   - Verify the JWT secret matches between Odoo and odoo_api

4. **Authentication failures**
   - Verify odoo_api service is running
   - Check API URLs in configuration
   - Ensure credentials are correct

### Logs

Check Odoo server logs for detailed error messages:
- JWT verification errors
- API connection issues
- User creation problems

## Best Practices

1. Use strong JWT secret keys
2. Regularly rotate JWT secrets
3. Monitor authentication logs
4. Use HTTPS in production
5. Implement proper error handling in client applications