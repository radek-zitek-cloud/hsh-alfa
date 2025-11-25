# Google OAuth2 Setup Guide

This guide will walk you through setting up Google OAuth2 authentication for the Home Sweet Home application.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Create a Google Cloud Project](#create-a-google-cloud-project)
3. [Enable Google OAuth2 API](#enable-google-oauth2-api)
4. [Create OAuth2 Credentials](#create-oauth2-credentials)
5. [Configure OAuth Consent Screen](#configure-oauth-consent-screen)
6. [Configure Application](#configure-application)
7. [Authorized Origins and Redirect URIs](#authorized-origins-and-redirect-uris)
8. [Testing](#testing)
9. [Production Deployment](#production-deployment)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- A Google account
- Access to [Google Cloud Console](https://console.cloud.google.com/)
- Home Sweet Home application running locally or deployed

---

## Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top of the page
3. Click **"New Project"**
4. Enter a project name (e.g., "Home Sweet Home")
5. Click **"Create"**
6. Wait for the project to be created and select it

---

## Enable Google OAuth2 API

1. In the Google Cloud Console, navigate to **"APIs & Services"** > **"Library"**
2. Search for **"Google+ API"** or **"Google Identity"**
3. Click on **"Google+ API"** (or "Google Identity Services")
4. Click **"Enable"**

---

## Configure OAuth Consent Screen

Before creating credentials, you need to configure the OAuth consent screen:

1. Navigate to **"APIs & Services"** > **"OAuth consent screen"**
2. Select **User Type**:
   - **Internal**: Only for Google Workspace users (if your organization uses Google Workspace)
   - **External**: For anyone with a Google account (recommended for personal use)
3. Click **"Create"**

### Fill in App Information:

1. **App name**: `Home Sweet Home` (or your preferred name)
2. **User support email**: Your email address
3. **App logo**: (Optional) Upload your app logo
4. **App domain**: (Optional for development)
   - Homepage: `http://localhost:3000` (for local development)
   - Privacy Policy: (Optional)
   - Terms of Service: (Optional)
5. **Authorized domains**:
   - For local development, leave empty
   - For production, add your domain (e.g., `example.com`)
6. **Developer contact information**: Your email address
7. Click **"Save and Continue"**

### Configure Scopes:

1. Click **"Add or Remove Scopes"**
2. Add the following scopes:
   - `openid`
   - `email`
   - `profile`
3. These scopes should be automatically selected. If not, search for them and add them.
4. Click **"Update"**
5. Click **"Save and Continue"**

### Test Users (for External apps):

1. If you selected "External" user type and your app is in testing mode:
   - Click **"Add Users"**
   - Add email addresses of users who should be able to test the app
   - Click **"Add"**
2. Click **"Save and Continue"**

### Summary:

1. Review your configuration
2. Click **"Back to Dashboard"**

---

## Create OAuth2 Credentials

1. Navigate to **"APIs & Services"** > **"Credentials"**
2. Click **"Create Credentials"** > **"OAuth client ID"**
3. Select **Application type**: **"Web application"**
4. Enter a **Name**: `Home Sweet Home Web Client` (or your preferred name)

### Configure Authorized JavaScript Origins:

Add the following origins based on your environment:

#### For Local Development:
```
http://localhost:3000
http://localhost:5173
http://localhost:8080
```

#### For Production:
```
https://your-domain.com
https://www.your-domain.com
```

**Note**: Replace `your-domain.com` with your actual domain.

### Configure Authorized Redirect URIs:

Add the following redirect URIs based on your environment:

#### For Local Development:
```
http://localhost:3000/auth/callback
http://localhost:5173/auth/callback
http://localhost:8080/auth/callback
```

#### For Production:
```
https://your-domain.com/auth/callback
https://www.your-domain.com/auth/callback
```

**Note**: Replace `your-domain.com` with your actual domain.

5. Click **"Create"**

### Save Your Credentials:

You will see a dialog with your credentials:
- **Client ID**: `xxxxx.apps.googleusercontent.com`
- **Client Secret**: `xxxxxxxxxxxxxxxx`

**IMPORTANT**: Copy these values immediately! You'll need them for the application configuration.

---

## Configure Application

### 1. Copy Environment Variables:

```bash
cp .env.example .env
```

### 2. Edit `.env` file:

Open the `.env` file and update the following variables:

```env
# OAuth2 Configuration (Google OAuth2)
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/callback

# JWT Configuration
# Generate a secure random key using:
# python -c 'import secrets; print(secrets.token_urlsafe(32))'
JWT_SECRET_KEY=your-secure-random-jwt-secret-key-here

# Frontend URL (used for OAuth2 redirects)
FRONTEND_URL=http://localhost:3000

# Security - IMPORTANT: Change this in production!
SECRET_KEY=your-secure-random-secret-key-here
```

### 3. Generate Secure Keys:

Generate secure random keys for `JWT_SECRET_KEY` and `SECRET_KEY`:

```bash
# Generate JWT_SECRET_KEY
python -c 'import secrets; print(secrets.token_urlsafe(32))'

# Generate SECRET_KEY
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

Copy the generated keys and paste them into your `.env` file.

---

## Authorized Origins and Redirect URIs

### Summary of Required URLs

#### Development Environment:

**Authorized JavaScript Origins:**
- `http://localhost:3000` (Frontend - default)
- `http://localhost:5173` (Vite dev server)
- `http://localhost:8080` (Alternative frontend port)

**Authorized Redirect URIs:**
- `http://localhost:3000/auth/callback`
- `http://localhost:5173/auth/callback`
- `http://localhost:8080/auth/callback`

#### Production Environment:

**Authorized JavaScript Origins:**
- `https://your-domain.com`
- `https://www.your-domain.com` (if using www subdomain)

**Authorized Redirect URIs:**
- `https://your-domain.com/auth/callback`
- `https://www.your-domain.com/auth/callback` (if using www subdomain)

**Important Notes:**
- Replace `your-domain.com` with your actual domain
- Always use HTTPS in production
- The redirect URI must exactly match the configured value
- You can have multiple origins and redirect URIs for different environments

---

## Testing

### 1. Start the Application:

```bash
# If using Docker Compose
docker-compose up -d

# Or for local development
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (in another terminal)
cd frontend
npm install
npm run dev
```

### 2. Test Authentication:

1. Open your browser and navigate to `http://localhost:3000`
2. You should see the login page
3. Click **"Sign in with Google"**
4. You'll be redirected to Google's login page
5. Sign in with your Google account
6. Grant permissions when prompted
7. You should be redirected back to the application and logged in

### 3. Verify User Session:

1. After logging in, you should see:
   - Your profile picture (if available)
   - Your name or email in the header
   - A logout button
2. Bookmarks and widgets should be accessible
3. Try logging out and logging back in

---

## Production Deployment

### 1. Update Google OAuth2 Credentials:

1. Go back to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **"APIs & Services"** > **"Credentials"**
3. Click on your OAuth 2.0 Client ID
4. Add your production URLs to:
   - **Authorized JavaScript origins**: `https://your-domain.com`
   - **Authorized redirect URIs**: `https://your-domain.com/auth/callback`
5. Click **"Save"**

### 2. Update Environment Variables:

Update your production `.env` file:

```env
# OAuth2 Configuration
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here
GOOGLE_REDIRECT_URI=https://your-domain.com/auth/callback

# JWT Configuration
JWT_SECRET_KEY=your-secure-production-jwt-secret-key

# Frontend URL
FRONTEND_URL=https://your-domain.com

# Security
SECRET_KEY=your-secure-production-secret-key

# Debug mode - IMPORTANT: Set to false in production
DEBUG=false
```

### 3. Verify OAuth Consent Screen:

1. If your app is still in "Testing" mode:
   - Navigate to **"APIs & Services"** > **"OAuth consent screen"**
   - Click **"Publish App"** to make it available to all users
   - Or add specific test users if you want to keep it in testing mode

### 4. Security Best Practices:

- ✅ Always use HTTPS in production
- ✅ Use strong, randomly generated secret keys
- ✅ Set `DEBUG=false` in production
- ✅ Regularly rotate your secret keys
- ✅ Keep your `GOOGLE_CLIENT_SECRET` secure and never commit it to version control
- ✅ Use environment-specific `.env` files (don't use the same keys in dev and prod)
- ✅ Set up proper CORS origins (don't use `CORS_ORIGINS=*` in production)

---

## Troubleshooting

### Error: "redirect_uri_mismatch"

**Problem**: The redirect URI doesn't match what's configured in Google Cloud Console.

**Solution**:
1. Check that the `GOOGLE_REDIRECT_URI` in your `.env` file exactly matches one of the authorized redirect URIs in Google Cloud Console
2. Make sure there are no trailing slashes or typos
3. Verify the protocol (http vs https) matches
4. Restart your application after changing the `.env` file

### Error: "Access blocked: This app's request is invalid"

**Problem**: The OAuth consent screen is not properly configured or the app is not published.

**Solution**:
1. Verify the OAuth consent screen is fully configured
2. If the app is in "Testing" mode, make sure your Google account is added as a test user
3. Consider publishing the app if it's ready for general use

### Error: "invalid_client"

**Problem**: The client ID or client secret is incorrect.

**Solution**:
1. Double-check your `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in the `.env` file
2. Make sure there are no extra spaces or line breaks
3. Verify you copied the entire client ID and secret from Google Cloud Console

### Error: "Authentication failed: 401 Unauthorized"

**Problem**: JWT secret key mismatch or expired token.

**Solution**:
1. Verify `JWT_SECRET_KEY` is set in your `.env` file
2. Make sure the key is the same between backend restarts
3. Clear your browser's local storage and try logging in again
4. Check backend logs for more specific error messages

### Login Page Shows Continuously

**Problem**: The frontend can't reach the backend API or authentication is failing silently.

**Solution**:
1. Check that the backend is running: `curl http://localhost:8000/health`
2. Check browser console for any errors
3. Verify API proxy settings in `vite.config.js`
4. Check that all environment variables are set correctly
5. Restart both frontend and backend services

### Users Can't Access After Login

**Problem**: CORS or cookie/token issues.

**Solution**:
1. Check CORS settings in backend `config.py`
2. Verify frontend URL is in `CORS_ORIGINS`
3. Clear browser cache and cookies
4. Check browser console for CORS errors
5. Ensure `FRONTEND_URL` matches your actual frontend URL

---

## Architecture Notes

### Multi-User Consideration

As per the MVP requirements:
- **Current**: All users share the same bookmarks and widgets data
- **Future**: The application is architected to support per-user data:
  - User model includes `id` field for future relationships
  - Database migrations are in place for user management
  - Authentication system is ready for per-user authorization

To enable per-user data in the future:
1. Add `user_id` foreign key columns to `bookmarks` and `widgets` tables
2. Update API endpoints to filter by `current_user.id`
3. Update service layer to scope queries by user
4. No frontend changes required - authentication is already in place

---

## Additional Resources

- [Google OAuth2 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Cloud Console](https://console.cloud.google.com/)
- [OAuth2 Best Practices](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)

---

## Support

If you encounter issues not covered in this guide:
1. Check the application logs (`docker-compose logs -f` or check individual service logs)
2. Verify all environment variables are set correctly
3. Ensure Google Cloud credentials are valid and not expired
4. Check that your Google account has the necessary permissions

For additional help, please refer to the main README or open an issue in the repository.
