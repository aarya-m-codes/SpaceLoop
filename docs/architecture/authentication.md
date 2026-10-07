# SpaceLoop Authentication & Multi-Factor Authentication (MFA) Architecture

SpaceLoop implements a production-grade, zero-trust authentication architecture featuring RFC 6238 Time-Based One-Time Password (TOTP) Multi-Factor Authentication, encrypted secrets at rest, cryptographically hashed emergency recovery codes, token separation, replay protection, and server-side policy enforcement.

---

## 1. MFA Security Model & State Transitions

The authentication subsystem strictly isolates intermediate authentication states, preventing partially authenticated users from accessing protected resources:

```
[ Unauthenticated Client ]
          │
          │ 1. POST /api/v1/auth/login (email + password)
          ▼
┌─────────────────────────────────┐
│ Primary Password Verification   │
└─────────────────────────────────┘
          │
    ┌─────┴────────────────────────┐
    │ MFA Disabled                 │ MFA Enabled
    ▼                              ▼
┌──────────────────────────┐   ┌──────────────────────────────────────────────┐
│ FULLY AUTHENTICATED      │   │ MFA REQUIRED (Pre-Authentication State)      │
│ Access Token (Bearer)    │   │ Token: type="mfa_pending", TTL=5 minutes     │
│ Refresh Token            │   │ 401 on all protected endpoints (@require_auth)│
│ Session Cookie (HttpOnly)│   └──────────────────────────────────────────────┘
└──────────────────────────┘                      │
                                                  │ 2. POST /api/v1/auth/mfa/verify
                                                  │    (TOTP or Recovery Code)
                                                  ▼
                                       ┌──────────────────────────┐
                                       │ FULLY AUTHENTICATED      │
                                       │ Access Token (type=access)│
                                       │ Refresh Token            │
                                       │ Session Cookie (HttpOnly)│
                                       └──────────────────────────┘
```

### Server-Side Token Isolation
- **`mfa_pending` Token**: Short-lived (5-minute TTL) JWT containing `sub` (User ID) and claim `type: "mfa_pending"`.
- **Enforcement**: Decorator `@require_auth` invokes `resolve_authenticated_user()`, which executes `decode_jwt(token, expected_type="access")`. An `mfa_pending` token is unconditionally rejected with HTTP 401 `UNAUTHORIZED`.
- **Bypass Prevention**: Client-side state changes, cookie manipulation, or header spoofing cannot bypass this server-side validation.

---

## 2. TOTP Implementation (RFC 6238)

- **Standard**: RFC 6238 compliant TOTP using HMAC-SHA1 with 30-second time steps and 6-digit dynamic truncation.
- **Secret Generation**: Cryptographically secure 20-byte random secrets (`secrets.token_bytes(20)`), Base32-encoded.
- **Protection at Rest**: Plaintext Base32 secrets are encrypted at rest using **Fernet (AES-128-CBC + HMAC-SHA256)** derived from `MFA_ENCRYPTION_KEY` or `SECRET_KEY`. Plaintext secrets are never stored in the database.
- **Provisioning URI**: Generates `otpauth://totp/SpaceLoop:<email>?secret=<b32>&issuer=SpaceLoop&algorithm=SHA1&digits=6&period=30` compatible with Google Authenticator, 1Password, Authy, Apple Keychain, etc.
- **Clock Drift**: Accommodates $\pm 1$ step (30 seconds) clock drift.
- **Replay Protection**: Successfully verified TOTP codes are cached with a 90-second TTL (`totp_replayed:<context>:<user_id>:<code>`). Replaying the same code within the time window is rejected with HTTP 401.

---

## 3. Emergency Backup Recovery Codes

- **Quantity & Format**: 8 high-entropy, human-readable codes formatted as `XXXXX-XXXXX` from an unambiguous alphanumeric alphabet (`ABCDEFGHJKLMNPQRSTUVWXYZ23456789`).
- **Hashing at Rest**: Plaintext codes are displayed to the user only once upon generation. Stored exclusively as normalized SHA-256 digests (`MFARecoveryCode.code_hash`).
- **Atomic Single-Use Consumption**: Consumption executes an atomic database update:
  ```python
  MFARecoveryCode.query.filter_by(user_id=user.id, code_hash=code_h, is_used=False).update(
      {"is_used": True, "used_at": utc_now()}, synchronize_session="fetch"
  )
  ```
  Concurrently raced requests for the same code will result in exactly 1 success and 1 rejection (no double-spend).
- **Regeneration**: `POST /api/v1/auth/mfa/recovery-codes/regenerate` requires current password + current TOTP code. Successfully regenerating immediately deletes all old recovery codes and commits 8 new hashed codes.

---

## 4. Enrollment & Disablement Lifecycles

### Enrollment Atomicity
1. User requests setup: `POST /api/v1/auth/mfa/setup`. Server stages secret in `user.mfa_pending_secret`. `user.mfa_enabled` remains `False`.
2. User scans QR or enters manual key into authenticator app.
3. User confirms proof of possession: `POST /api/v1/auth/mfa/verify-setup` with current 6-digit TOTP.
4. Server verifies code against `mfa_pending_secret`. Only on success is `user.mfa_secret` activated, `user.mfa_pending_secret` cleared, and `user.mfa_enabled = True`.
5. If verification fails or is aborted, MFA remains completely disabled and pending secrets are discarded.

### Disablement Re-Authentication
- `POST /api/v1/auth/mfa/disable` strictly forbids disabling MFA with password alone.
- Requires:
  1. Valid account password.
  2. Valid current TOTP code OR unconsumed backup recovery code.
- Upon successful disablement:
  - `user.mfa_enabled = False`
  - `user.mfa_secret = None`
  - All recovery codes deleted from database.
  - Active device sessions revoked (`invalidate_user_session`).

---

## 5. Security Guardrails & Policy Enforcement

| Vector | Defense Mechanism |
|---|---|
| **Brute-Force Attacks** | Sliding window rate limits per IP and account (max 5 failed MFA attempts / 15 min $\to$ HTTP 429). |
| **Password Reset Bypass** | Resetting password (`/api/v1/auth/reset-password`) preserves `mfa_enabled` and `mfa_secret`. Subsequent login still strictly requires second factor. |
| **Refresh Token Abuse** | Refresh endpoint (`/api/v1/auth/refresh`) requires `type="refresh"`. Passing `mfa_pending` token returns HTTP 401. |
| **Privileged Admin Accounts** | `@require_admin` decorator checks `MFA_ENFORCE_ADMIN` policy. Unconfigured admin accounts are rejected with 403 `MFA_REQUIRED_FOR_ADMIN`. |
| **Secret Leakage** | `User.to_dict()` excludes `mfa_secret` and `mfa_pending_secret`. Audit logs record method type without logging codes or secrets. |
| **Session Fixation** | Final authentication rotates session identifiers and issues fresh cryptographically signed device sessions. |

---

## 6. Verification & Automated Test Scenarios

The test suite in `tests/test_mfa_foolproof_security.py` verifies all 26 scenarios (A through Z):

- **Scenario A**: MFA disabled login $\to$ immediate access token.
- **Scenario B**: MFA enabled login $\to$ `mfa_required=True` with restricted `mfa_token`.
- **Scenario C**: Valid TOTP code completes authentication.
- **Scenario D**: Invalid TOTP code denied (HTTP 401).
- **Scenario E**: Expired TOTP code outside window denied (HTTP 401).
- **Scenario F**: Replayed TOTP code within same window rejected (HTTP 401).
- **Scenario G**: Brute-force verification attempts trigger rate limiting (HTTP 429).
- **Scenario H**: Valid emergency recovery code completes authentication.
- **Scenario I**: Replay of consumed recovery code rejected (HTTP 401).
- **Scenario J**: Recovery code regeneration invalidates old codes and activates new ones.
- **Scenario K**: Enrollment atomicity: secret staged $\to$ unactivated until TOTP verification.
- **Scenario L**: Enrollment failure leaves MFA disabled.
- **Scenario M**: Disable attempt without reauthentication rejected (HTTP 400/401).
- **Scenario N**: Valid reauthentication disables MFA and revokes sessions.
- **Scenario O**: `mfa_pending` token blocked from protected endpoints (HTTP 401).
- **Scenario P**: Manipulated or forged token signatures rejected (HTTP 401).
- **Scenario Q**: Direct API calls bypassing frontend strictly enforced server-side.
- **Scenario R**: Password reset preserves MFA requirement for subsequent logins.
- **Scenario S**: Refresh token endpoint rejects `mfa_pending` tokens.
- **Scenario T**: Logout invalidates session and clears cookies.
- **Scenario U**: Device session revocation marks records inactive.
- **Scenario V**: Concurrent recovery code submissions resolve atomically (1 success, 1 fail).
- **Scenario W**: Profile endpoints and audit logs do not leak secrets or OTPs.
- **Scenario X**: Privileged admin MFA enforcement policy blocks non-MFA admins.
- **Scenario Y**: Application restart preserves encrypted secrets and decryptability.
- **Scenario Z**: End-to-end user lifecycle: register $\to$ login $\to$ enroll $\to$ logout $\to$ login $\to$ challenge $\to$ dashboard.
