# passwordless-auth-service
Authentication and Authorization for services running on the same docker bridge network.

## Features
- 🔒 Passwordless authentication using device-bound HMAC cookies
- 🔐 TOTP-based device registration
- 🧠 Stateless service authorization via `/verify/<service>`
- 🔄 Scalable microservice-compatible design
- 🐳 Docker-ready with `.env` support

## Workflow
The user logs in via the open `/login` path, which internally calls `/device/add` and responds with authentication cookies. These cookies are HTTPS-only and domain-scoped. Once set, the client can make authenticated requests to services using the cookies.
Service requests trigger internal calls to `/verify/<service>`, which confirms both the cookie's validity and the user's permission to access the specific service.

![Auth diagram](https://github.com/user-attachments/assets/ff25884f-651e-48cf-8d41-9eb5dbf2c341)

**Security note:** The `/verify/<service>` endpoint is only accessible within the internal Docker network. The `/device/add` route always returns a generic `401 Unauthorized` on failure, regardless of whether the email or TOTP code was incorrect — preventing information disclosure about valid accounts.
**Error handling:**

The `/verify/<service>` endpoint uses carefully scoped status codes based on authentication and authorization state:

- `404 Not Found` — returned when the request is **unauthenticated** (i.e., invalid or missing cookies); this avoids leaking any information about services or user validity
- `404 Not Found` with body `"Service Not Found!"` — returned when the user is authenticated, but the requested service does not exist
- `401 Unauthorized` with body `"User does not have access to this service"` — returned when the user is authenticated, the service exists, but they lack access rights

This design ensures public-facing services (which forward auth cookies to FlaskAuth) never reveal whether a given user or service is valid unless the user is already fully authenticated. It mirrors the login behavior and preserves information boundaries without sacrificing debuggability for valid users.

## Structure
The database is structured as the shown Entity Relationship diagram, with `/verify/<service>` being successful with `200` for all users with a connection between to the Service in UserService.

![Entity Relationship Diagram Auth-service (UML Notation)](https://github.com/user-attachments/assets/b7d94e33-6610-40fe-b214-22b51233d905)


## 🔐 Security Considerations

This system is designed with layered security in mind. Several common attack vectors are mitigated as follows:

### ✅ Core Defenses

- **SQL Injection**: All SQL statements use parameterized queries via Python’s MySQL libraries.
- **Closed network Seperations**: Only paths necessary for login are public to a user, with /verify/<service> available to services on the internal docker network.
- **Environment Secrets**: All critical secrets (encryption keys etc.) are sourced from environment variables.
- **Timing Attacks**: Device verification always performs cryptographic operations (e.g., HMAC) even on failure, to avoid measurable timing differences.
- **DoS Mitigation**: Expired or invalid cookies are discarded early in the request cycle to avoid unnecessary computation.
- **Information Leakage**: Authentication routes always respond with generic `401 Unauthorized` responses regardless of specific failure reasons, preventing user enumeration.
- **Database Leakage**:  
  - TOTP secrets are encrypted using Fernet and not stored in plaintext.  
  - Device HMACs store only the **signature**, not the secret.  
  - Service tokens are **salted and hashed**.  
  - `UserServiceTokens` are **encrypted**, preventing direct association between users and services even if both DBs are leaked.
- **Service Abuse**: Only services presenting valid, pre-registered service tokens can access `/verify/<service>`.
- **TOTP Secret Protection**: Secrets are encrypted at rest using Fernet. Without access to the environment key, they cannot be recovered.
- **Scoped Authorization**: Services only receive a `UserServiceToken` identifier, without access to user identity or metadata.

---

### 🔒 TLS Considerations

When deployed behind HTTPS (as recommended):

- **Session Hijacking**: Cookies are transmitted securely using the `Secure`, `HttpOnly`, and `SameSite=None` flags.
- **Replay Attacks**: The system resists replay by using long-lived device pairing and scoped service tokens, not short-lived logins.

---

### 🌐 Cloudflare Integration (Optional)

When deployed behind Cloudflare:

- **DDoS Protection**: Cloudflare's global edge protects the authentication endpoint from volumetric attacks.
- **Bot Detection**: Malicious and suspicious traffic is filtered before reaching the backend.

---

### 🛡️ Additional Hardening (Optional)

For further security, consider:

- **Fail2ban**: Monitor failed attempts via logs and ban IPs on abusive behavior.
- **Rate Limiting**: Enforce request limits per IP or token to limit brute-force attempts.
- **Audit Logging**: Track key auth events (e.g., token issuance, failed attempts).


## Setup
The service is generally intended for running on Docker on a bridge network closed for the services. This can be run by updating the ```.env.example``` and the ```docker-compose``` to match the network bridge and then ```docker-compose up --build```.
TOTP secrets can be used with any authenticator app. 

### Getting Started

## Reverse proxy
1. Copy `reverse_proxy/server.example.config` to `reverse_proxy/server.config` and update domain

## Database setup (Mysql) (optional)
1. Update `/mysqlbd/06-addUser.sql` with valid password for the user `FlaskAuth`. 
2. Run `/mysqlbd/setupDatabase.sh` - To create the database `Auth_service`, with all the tables, and user `FlaskAuth` with access to

## Server
1. Copy `.env.example` to `.env` and update values

**Note**: The `.env.testing` file contains public testing keys (e.g., `FLASK_SECRET`, `TOPT_ENCRYPTION_KEY`) required for test validation. These are **not secure** and must **not** be used in production. Do not copy `.env.testing` into `.env` — generate fresh secrets for real deployments.
   
2. Run `docker-compose up --build`
3. Use mysql or `admin.cli.py` to add Users, Services and UserServices 
4. Add/login to devices from `http://<host>:5000/login`

## Client
Example and some SDK's for client implementation can be found in the [ClientImplementation Folder](https://github.com/Jako4458/passwordless-auth-service/tree/master/ClientImplementation)

## Test (local)
1. Run `pip install -r test-requirements.txt` to install necessary python requirements  
2. Install docker
3. Run `python3 testing.py`
   
### Service permission
Service permission are by default granted to admin users while services are otherwise granted by adding a UserService instance connecting a User to a Service and verifying the connection based on the specific device cookies.  
