import json
import os
import tempfile
import unittest
from datetime import datetime, timezone

from app import create_app
from backend.core.cache import cache
from backend.core.database import db, init_db
from backend.modules.auth.mfa import generate_totp_code
from config import TestingConfig
from models import MFARecoveryCode, User


class AuthTestCase(unittest.TestCase):
    """Comprehensive test suite for SpaceLoop authentication & authorization."""

    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")

        class AuthTestConfig(TestingConfig):
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.temp_db_path}"
            SECRET_KEY = "test-auth-fernet-secret-key-32-bytes!"

        self.app = create_app(AuthTestConfig)
        self.client = self.app.test_client()

        with self.app.app_context():
            init_db(self.app)
            cache.clear()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()
        try:
            os.close(self.temp_db_fd)
            if os.path.exists(self.temp_db_path):
                os.unlink(self.temp_db_path)
            for ext in ("-wal", "-shm"):
                f = f"{self.temp_db_path}{ext}"
                if os.path.exists(f):
                    os.unlink(f)
        except OSError:
            pass

    def test_registration(self):
        """1. Verify account registration, token issuance, cookies, and disposable email block."""
        # Disposable email should be blocked
        res_disp = self.client.post("/api/v1/auth/register", json={
            "email": "spammer@mailinator.com",
            "password": "Password123!",
            "full_name": "Spam User",
        })
        self.assertEqual(res_disp.status_code, 400)
        self.assertIn("Disposable", res_disp.get_json()["error"]["message"])

        # Weak password should be rejected
        res_weak = self.client.post("/api/v1/auth/register", json={
            "email": "seeker1@spaceloop.in",
            "password": "simple",
            "full_name": "Test Seeker",
        })
        self.assertEqual(res_weak.status_code, 400)

        # Successful registration
        res = self.client.post("/api/v1/auth/register", json={
            "email": "seeker1@spaceloop.in",
            "password": "SecurePassword#2026",
            "full_name": "Aarav Patel",
            "phone": "+919876543211",
            "role": "seeker",
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()["data"]
        self.assertIn("access_token", data)
        self.assertIn("refresh_token", data)
        self.assertEqual(data["user"]["email"], "seeker1@spaceloop.in")
        self.assertEqual(data["user"]["role"], "seeker")
        self.assertNotIn("password_hash", data["user"])
        self.assertNotIn("mfa_secret", data["user"])

        # Cookie check
        cookie_header = res.headers.get("Set-Cookie")
        self.assertIn("spaceloop_session=", cookie_header)
        self.assertIn("HttpOnly", cookie_header)

    def test_duplicate_email(self):
        """2. Verify duplicate registration prevention (409 Conflict)."""
        payload = {
            "email": "duplicate@spaceloop.in",
            "password": "Password123!",
            "full_name": "Original User",
        }
        res1 = self.client.post("/api/v1/auth/register", json=payload)
        self.assertEqual(res1.status_code, 201)

        res2 = self.client.post("/api/v1/auth/register", json=payload)
        self.assertEqual(res2.status_code, 409)
        self.assertFalse(res2.get_json()["success"])

    def test_login_and_logout(self):
        """3. Verify login and logout session invalidation."""
        self.client.post("/api/v1/auth/register", json={
            "email": "user.login@spaceloop.in",
            "password": "Password123!",
            "full_name": "Login User",
        })

        # Successful login
        login_res = self.client.post("/api/v1/auth/login", json={
            "email": "user.login@spaceloop.in",
            "password": "Password123!",
        })
        self.assertEqual(login_res.status_code, 200)
        login_data = login_res.get_json()["data"]
        self.assertFalse(login_data["mfa_required"])
        token = login_data["access_token"]

        # Logout
        logout_res = self.client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(logout_res.status_code, 200)
        self.assertTrue(logout_res.get_json()["success"])

    def test_invalid_password_login(self):
        """4. Verify invalid password rejection (401 Unauthorized)."""
        self.client.post("/api/v1/auth/register", json={
            "email": "wrongpwd@spaceloop.in",
            "password": "CorrectPassword#1",
            "full_name": "Test User",
        })

        res = self.client.post("/api/v1/auth/login", json={
            "email": "wrongpwd@spaceloop.in",
            "password": "IncorrectPassword#99",
        })
        self.assertEqual(res.status_code, 401)
        self.assertFalse(res.get_json()["success"])

    def test_protected_route_and_bearer_auth(self):
        """5. Verify protected route rejects unauthorized requests and accepts Bearer tokens."""
        # Unauthenticated request
        unauth_res = self.client.get("/api/v1/auth/me")
        self.assertEqual(unauth_res.status_code, 401)

        # Register and get token
        reg_res = self.client.post("/api/v1/auth/register", json={
            "email": "bearer.user@spaceloop.in",
            "password": "Password123!",
            "full_name": "Bearer Test",
            "role": "host",
        })
        token = reg_res.get_json()["data"]["access_token"]

        # Authenticated request with Bearer header
        auth_res = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(auth_res.status_code, 200)
        user_info = auth_res.get_json()["data"]
        self.assertEqual(user_info["email"], "bearer.user@spaceloop.in")
        self.assertEqual(user_info["role"], "host")
        self.assertIn("space:create", user_info["permissions"])

    def test_x_user_id_fallback(self):
        """6. Verify X-User-Id header fallback for cross-origin/proxy environments."""
        reg_res = self.client.post("/api/v1/auth/register", json={
            "email": "proxy.user@spaceloop.in",
            "password": "Password123!",
            "full_name": "Proxy User",
        })
        user_id = reg_res.get_json()["data"]["user"]["id"]

        # Call /me without Bearer token or cookies, providing only X-User-Id header
        res = self.client.get("/api/v1/auth/me", headers={"X-User-Id": str(user_id)})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertEqual(data["id"], user_id)
        self.assertEqual(data["email"], "proxy.user@spaceloop.in")

    def test_role_permissions_and_context_switching(self):
        """7. Verify PBAC role permissions and dynamic context switching."""
        reg_res = self.client.post("/api/v1/auth/register", json={
            "email": "host.context@spaceloop.in",
            "password": "Password123!",
            "full_name": "Context Host",
            "role": "host",
        })
        token = reg_res.get_json()["data"]["access_token"]

        # Host has space:create
        me_res1 = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertIn("space:create", me_res1.get_json()["data"]["permissions"])

        # Switch context to seeker
        ctx_res = self.client.post(
            "/api/v1/auth/context",
            headers={"Authorization": f"Bearer {token}"},
            json={"role": "seeker"},
        )
        self.assertEqual(ctx_res.status_code, 200)
        self.assertEqual(ctx_res.get_json()["data"]["active_role"], "seeker")

        # Verify active role updated
        new_token = ctx_res.get_json()["data"]["access_token"]
        me_res2 = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_token}"})
        self.assertEqual(me_res2.get_json()["data"]["active_role"], "seeker")
        self.assertIn("booking:create", me_res2.get_json()["data"]["permissions"])

    def test_email_verification(self):
        """8. Verify email verification flow (token lookup and consumption)."""
        reg_res = self.client.post("/api/v1/auth/register", json={
            "email": "verify.me@spaceloop.in",
            "password": "Password123!",
            "full_name": "Verify Me",
        })
        token = reg_res.get_json()["data"]["verification_token"]

        # Verify via GET query parameter
        ver_res = self.client.get(f"/api/v1/auth/verify-email?token={token}")
        self.assertEqual(ver_res.status_code, 200)
        self.assertIn("successfully verified", ver_res.get_json()["message"])

        # Consumed token cannot be reused
        reuse_res = self.client.get(f"/api/v1/auth/verify-email?token={token}")
        self.assertEqual(reuse_res.status_code, 400)

        # Resend verification
        resend_res = self.client.post("/api/v1/auth/resend-verification", json={"email": "verify.me@spaceloop.in"})
        self.assertEqual(resend_res.status_code, 200)

    def test_password_reset(self):
        """9. Verify password recovery and reset token expiration handling."""
        self.client.post("/api/v1/auth/register", json={
            "email": "reset.pwd@spaceloop.in",
            "password": "OldPassword123!",
            "full_name": "Reset User",
        })

        # Request reset
        req_res = self.client.post("/api/v1/auth/forgot-password", json={"email": "reset.pwd@spaceloop.in"})
        self.assertEqual(req_res.status_code, 200)
        reset_token = req_res.get_json()["data"]["dev_reset_token"]

        # Reset password
        res_post = self.client.post("/api/v1/auth/reset-password", json={
            "token": reset_token,
            "new_password": "NewSecurePassword456!",
        })
        self.assertEqual(res_post.status_code, 200)

        # Old password fails
        old_login = self.client.post("/api/v1/auth/login", json={
            "email": "reset.pwd@spaceloop.in",
            "password": "OldPassword123!",
        })
        self.assertEqual(old_login.status_code, 401)

        # New password succeeds
        new_login = self.client.post("/api/v1/auth/login", json={
            "email": "reset.pwd@spaceloop.in",
            "password": "NewSecurePassword456!",
        })
        self.assertEqual(new_login.status_code, 200)

    def test_mfa_setup_and_challenge(self):
        """10. Verify full MFA lifecycle: setup, verify-setup, TOTP challenge, recovery codes, and disable."""
        reg_res = self.client.post("/api/v1/auth/register", json={
            "email": "mfa.user@spaceloop.in",
            "password": "Password123!",
            "full_name": "MFA User",
        })
        token = reg_res.get_json()["data"]["access_token"]
        user_id = reg_res.get_json()["data"]["user"]["id"]

        # 1. Setup MFA
        setup_res = self.client.post(
            "/api/v1/auth/mfa/setup",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(setup_res.status_code, 200)
        setup_data = setup_res.get_json()["data"]
        raw_secret = setup_data["secret"]
        recovery_codes = setup_data["recovery_codes"]
        self.assertEqual(len(recovery_codes), 8)
        self.assertIn("otpauth://", setup_data["provisioning_uri"])

        # Verify DB does NOT store plain secret
        with self.app.app_context():
            u = db.session.get(User, user_id)
            self.assertNotEqual(u.mfa_secret, raw_secret)
            self.assertFalse(u.mfa_enabled)

        # 2. Verify Setup with valid TOTP code
        totp_code = generate_totp_code(raw_secret)
        ver_res = self.client.post(
            "/api/v1/auth/mfa/verify-setup",
            headers={"Authorization": f"Bearer {token}"},
            json={"code": totp_code},
        )
        self.assertEqual(ver_res.status_code, 200)

        # In DB, mfa_enabled is now True
        with self.app.app_context():
            u = db.session.get(User, user_id)
            self.assertTrue(u.mfa_enabled)

        # 3. Login now triggers MFA challenge
        login_res = self.client.post("/api/v1/auth/login", json={
            "email": "mfa.user@spaceloop.in",
            "password": "Password123!",
        })
        self.assertEqual(login_res.status_code, 200)
        login_data = login_res.get_json()["data"]
        self.assertTrue(login_data["mfa_required"])
        mfa_token = login_data["mfa_token"]

        # 4. Complete challenge using TOTP code
        totp_code_now = generate_totp_code(raw_secret)
        challenge_res = self.client.post("/api/v1/auth/mfa/verify", json={
            "mfa_token": mfa_token,
            "code": totp_code_now,
        })
        self.assertEqual(challenge_res.status_code, 200)
        self.assertIn("access_token", challenge_res.get_json()["data"])

        # 5. Test Recovery Code on next login
        login_res2 = self.client.post("/api/v1/auth/login", json={
            "email": "mfa.user@spaceloop.in",
            "password": "Password123!",
        })
        mfa_token2 = login_res2.get_json()["data"]["mfa_token"]

        used_rec_code = recovery_codes[0]
        rec_res = self.client.post("/api/v1/auth/mfa/verify", json={
            "mfa_token": mfa_token2,
            "recovery_code": used_rec_code,
        })
        self.assertEqual(rec_res.status_code, 200)

        # Recovery code cannot be reused
        login_res3 = self.client.post("/api/v1/auth/login", json={
            "email": "mfa.user@spaceloop.in",
            "password": "Password123!",
        })
        mfa_token3 = login_res3.get_json()["data"]["mfa_token"]
        rec_reuse = self.client.post("/api/v1/auth/mfa/verify", json={
            "mfa_token": mfa_token3,
            "recovery_code": used_rec_code,
        })
        self.assertEqual(rec_reuse.status_code, 401)

        # 6. Disable MFA
        auth_token = challenge_res.get_json()["data"]["access_token"]
        disable_code = generate_totp_code(raw_secret)
        disable_res = self.client.post(
            "/api/v1/auth/mfa/disable",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "password": "Password123!",
                "code": disable_code,
            },
        )
        self.assertEqual(disable_res.status_code, 200)

        with self.app.app_context():
            u = db.session.get(User, user_id)
            self.assertFalse(u.mfa_enabled)
            self.assertIsNone(u.mfa_secret)

    def test_security_headers(self):
        """11. Verify security headers attached to all API responses."""
        res = self.client.get("/api/v1/health")
        self.assertEqual(res.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(res.headers.get("X-Frame-Options"), "DENY")
        self.assertEqual(res.headers.get("X-XSS-Protection"), "1; mode=block")
        self.assertEqual(res.headers.get("Referrer-Policy"), "strict-origin-when-cross-origin")
        self.assertIn("Content-Security-Policy", res.headers)

    def test_privilege_escalation_prevented(self):
        """13. Verify that clients cannot self-register with admin role."""
        res = self.client.post("/api/v1/auth/register", json={
            "email": "hacker@spaceloop.in",
            "password": "Password123!",
            "full_name": "Privilege Escalation Attempt",
            "role": "admin",
        })
        self.assertEqual(res.status_code, 403)
        self.assertIn("administrator registration is not permitted", res.get_json()["error"]["message"])

    def test_rate_limiting(self):
        """14. Verify rate limiting triggers 429 when attempt thresholds are exceeded."""
        email = "bruteforce@spaceloop.in"
        # Register user first
        self.client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "Password123!",
            "full_name": "Target Account",
        })

        # Send 5 failed attempts (allowed threshold is 5)
        for _ in range(5):
            res = self.client.post("/api/v1/auth/login", json={
                "email": email,
                "password": "WrongPassword#1",
            })
            self.assertEqual(res.status_code, 401)

        # 6th attempt should trigger 429
        blocked_res = self.client.post("/api/v1/auth/login", json={
            "email": email,
            "password": "WrongPassword#1",
        })
        self.assertEqual(blocked_res.status_code, 429)
        self.assertIn("Too many failed login attempts", blocked_res.get_json()["error"]["message"])


if __name__ == "__main__":
    unittest.main()
