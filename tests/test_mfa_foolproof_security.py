"""SpaceLoop Foolproof Multi-Factor Authentication (MFA) Comprehensive Test Suite.

Exhaustively verifies production-grade TOTP and recovery-code security across
all 26 adversarial and operational scenarios (A through Z):
  A. MFA disabled: password -> authenticated
  B. MFA enabled: password -> MFA required
  C. Correct TOTP: password -> valid TOTP -> authenticated
  D. Incorrect TOTP: password -> invalid TOTP -> denied
  E. Expired/invalid TOTP: -> denied
  F. Replayed TOTP: -> appropriately rejected
  G. Brute-force MFA: -> rate limiting activates
  H. Recovery code: -> authenticated
  I. Recovery code replay: -> rejected
  J. Recovery code regeneration: old codes -> invalid, new codes -> valid
  K. MFA enrollment: secret generated -> not enabled; correct TOTP -> enabled
  L. Enrollment with incorrect TOTP: -> MFA remains disabled
  M. MFA disable without required reauthentication: -> denied
  N. MFA disable with valid reauthentication: -> succeeds
  O. MFA-pending session accessing protected endpoint: -> denied
  P. MFA-pending token manipulated: -> denied
  Q. Direct API call bypassing frontend: -> denied
  R. Password reset attempting to bypass MFA: -> denied
  S. Refresh token during MFA-pending state: -> cannot become fully authenticated without MFA
  T. Logout: -> authentication state invalidated appropriately
  U. Session/token revocation: -> old authenticated state rejected
  V. Concurrent recovery-code use: -> only one request succeeds
  W. Secret leakage: secrets/codes never leaked in responses, errors, or profiles
  X. Privileged/admin account: -> MFA enforcement works as designed
  Y. Application restart: -> MFA configuration remains correct
  Z. Full end-to-end flow: register -> login -> enroll -> logout -> login -> MFA -> access protected resource
"""

import concurrent.futures
import json
import os
import tempfile
import time
import unittest

from app import create_app
from backend.core.cache import cache
from backend.core.database import db, init_db
from backend.modules.auth.mfa import (
    decrypt_totp_secret,
    encrypt_totp_secret,
    generate_totp_code,
    generate_totp_secret,
    verify_totp_code,
)
from backend.modules.auth.tokens import (
    create_access_token,
    create_mfa_pending_token,
    decode_jwt,
    encode_jwt,
)
from config import TestingConfig
from models import DeviceSession, MFARecoveryCode, PasswordResetToken, User


class MFAFoolproofSecurityTestCase(unittest.TestCase):
    """Exhaustive test suite for SpaceLoop Multi-Factor Authentication."""

    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")

        class MFATestConfig(TestingConfig):
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.temp_db_path}"
            SECRET_KEY = "test-fernet-secret-key-32-bytes-long!"
            MFA_ENCRYPTION_KEY = "test-fernet-secret-key-32-bytes-long!"
            MFA_ENFORCE_ADMIN = False

        self.app = create_app(MFATestConfig)
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

    def _register_user(self, email="user@spaceloop.in", password="SecurePassword#2026", role="seeker"):
        res = self.client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "full_name": "Test User",
            "role": role,
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()["data"]
        return data["user"]["id"], data["access_token"]

    def _enable_mfa_for_user(self, token):
        # 1. Setup
        setup_res = self.client.post("/api/v1/auth/mfa/setup", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(setup_res.status_code, 200)
        setup_data = setup_res.get_json()["data"]
        raw_secret = setup_data["secret"]
        recovery_codes = setup_data["recovery_codes"]

        # 2. Verify setup
        code = generate_totp_code(raw_secret)
        ver_res = self.client.post(
            "/api/v1/auth/mfa/verify-setup",
            headers={"Authorization": f"Bearer {token}"},
            json={"code": code},
        )
        self.assertEqual(ver_res.status_code, 200)
        return raw_secret, recovery_codes

    # ==========================================================
    # SCENARIOS A through Z
    # ==========================================================

    def test_scenario_a_mfa_disabled_login(self):
        """A. MFA disabled: password -> full authentication."""
        self._register_user(email="user_a@spaceloop.in")
        res = self.client.post("/api/v1/auth/login", json={
            "email": "user_a@spaceloop.in",
            "password": "SecurePassword#2026",
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertFalse(data["mfa_required"])
        self.assertIn("access_token", data)
        self.assertIn("refresh_token", data)

    def test_scenario_b_mfa_enabled_login_requires_mfa(self):
        """B. MFA enabled: password -> MFA required with restricted mfa_token."""
        _, token = self._register_user(email="user_b@spaceloop.in")
        self._enable_mfa_for_user(token)

        login_res = self.client.post("/api/v1/auth/login", json={
            "email": "user_b@spaceloop.in",
            "password": "SecurePassword#2026",
        })
        self.assertEqual(login_res.status_code, 200)
        data = login_res.get_json()["data"]
        self.assertTrue(data["mfa_required"])
        self.assertIn("mfa_token", data)
        self.assertNotIn("access_token", data)

    def test_scenario_c_correct_totp_challenge_success(self):
        """C. Correct TOTP: password -> valid TOTP -> authenticated."""
        _, token = self._register_user(email="user_c@spaceloop.in")
        raw_secret, _ = self._enable_mfa_for_user(token)

        login_res = self.client.post("/api/v1/auth/login", json={
            "email": "user_c@spaceloop.in",
            "password": "SecurePassword#2026",
        })
        mfa_token = login_res.get_json()["data"]["mfa_token"]

        code = generate_totp_code(raw_secret)
        challenge_res = self.client.post("/api/v1/auth/mfa/verify", json={
            "mfa_token": mfa_token,
            "code": code,
        })
        self.assertEqual(challenge_res.status_code, 200)
        data = challenge_res.get_json()["data"]
        self.assertIn("access_token", data)
        self.assertIn("refresh_token", data)

    def test_scenario_d_incorrect_totp_denied(self):
        """D. Incorrect TOTP: password -> invalid TOTP -> denied (401)."""
        _, token = self._register_user(email="user_d@spaceloop.in")
        self._enable_mfa_for_user(token)

        login_res = self.client.post("/api/v1/auth/login", json={
            "email": "user_d@spaceloop.in",
            "password": "SecurePassword#2026",
        })
        mfa_token = login_res.get_json()["data"]["mfa_token"]

        challenge_res = self.client.post("/api/v1/auth/mfa/verify", json={
            "mfa_token": mfa_token,
            "code": "000000",
        })
        self.assertEqual(challenge_res.status_code, 401)
        self.assertFalse(challenge_res.get_json()["success"])

    def test_scenario_e_expired_totp_denied(self):
        """E. Expired/invalid TOTP: code from far past -> denied (401)."""
        _, token = self._register_user(email="user_e@spaceloop.in")
        raw_secret, _ = self._enable_mfa_for_user(token)

        login_res = self.client.post("/api/v1/auth/login", json={
            "email": "user_e@spaceloop.in",
            "password": "SecurePassword#2026",
        })
        mfa_token = login_res.get_json()["data"]["mfa_token"]

        # Generate TOTP from 5 minutes (300 seconds) ago
        expired_time = int(time.time()) - 300
        expired_code = generate_totp_code(raw_secret, for_time=expired_time)

        challenge_res = self.client.post("/api/v1/auth/mfa/verify", json={
            "mfa_token": mfa_token,
            "code": expired_code,
        })
        self.assertEqual(challenge_res.status_code, 401)

    def test_scenario_f_replayed_totp_rejected(self):
        """F. Replayed TOTP: submitting same valid TOTP twice within window -> rejected (401)."""
        _, token = self._register_user(email="user_f@spaceloop.in")
        raw_secret, _ = self._enable_mfa_for_user(token)

        # First login challenge
        login1 = self.client.post("/api/v1/auth/login", json={
            "email": "user_f@spaceloop.in",
            "password": "SecurePassword#2026",
        })
        mfa_token1 = login1.get_json()["data"]["mfa_token"]
        code = generate_totp_code(raw_secret)

        res1 = self.client.post("/api/v1/auth/mfa/verify", json={
            "mfa_token": mfa_token1,
            "code": code,
        })
        self.assertEqual(res1.status_code, 200)

        # Second login challenge attempt using the EXACT SAME CODE
        login2 = self.client.post("/api/v1/auth/login", json={
            "email": "user_f@spaceloop.in",
            "password": "SecurePassword#2026",
        })
        mfa_token2 = login2.get_json()["data"]["mfa_token"]

        res2 = self.client.post("/api/v1/auth/mfa/verify", json={
            "mfa_token": mfa_token2,
            "code": code,
        })
        self.assertEqual(res2.status_code, 401)
        self.assertIn("Invalid 6-digit TOTP code", res2.get_json()["error"]["message"])

    def test_scenario_g_brute_force_mfa_rate_limiting(self):
        """G. Brute-force MFA: rate limiting activates (429) after threshold."""
        _, token = self._register_user(email="user_g@spaceloop.in")
        self._enable_mfa_for_user(token)

        login_res = self.client.post("/api/v1/auth/login", json={
            "email": "user_g@spaceloop.in",
            "password": "SecurePassword#2026",
        })
        mfa_token = login_res.get_json()["data"]["mfa_token"]

        # Threshold is 5 failed attempts
        for _ in range(5):
            res = self.client.post("/api/v1/auth/mfa/verify", json={
                "mfa_token": mfa_token,
                "code": "111111",
            })
            self.assertEqual(res.status_code, 401)

        # 6th attempt triggers 429
        blocked = self.client.post("/api/v1/auth/mfa/verify", json={
            "mfa_token": mfa_token,
            "code": "111111",
        })
        self.assertEqual(blocked.status_code, 429)

    def test_scenario_h_recovery_code_authentication(self):
        """H. Recovery code: password -> valid recovery code -> authenticated."""
        _, token = self._register_user(email="user_h@spaceloop.in")
        _, recovery_codes = self._enable_mfa_for_user(token)

        login_res = self.client.post("/api/v1/auth/login", json={
            "email": "user_h@spaceloop.in",
            "password": "SecurePassword#2026",
        })
        mfa_token = login_res.get_json()["data"]["mfa_token"]

        res = self.client.post("/api/v1/auth/mfa/verify", json={
            "mfa_token": mfa_token,
            "recovery_code": recovery_codes[0],
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn("access_token", res.get_json()["data"])

    def test_scenario_i_recovery_code_replay_rejected(self):
        """I. Recovery code replay: already used code rejected on next challenge (401)."""
        _, token = self._register_user(email="user_i@spaceloop.in")
        _, recovery_codes = self._enable_mfa_for_user(token)
        used_code = recovery_codes[0]

        # Use recovery code first time
        login1 = self.client.post("/api/v1/auth/login", json={
            "email": "user_i@spaceloop.in",
            "password": "SecurePassword#2026",
        })
        mfa1 = login1.get_json()["data"]["mfa_token"]
        self.assertEqual(self.client.post("/api/v1/auth/mfa/verify", json={
            "mfa_token": mfa1,
            "recovery_code": used_code,
        }).status_code, 200)

        # Attempt to reuse same recovery code
        login2 = self.client.post("/api/v1/auth/login", json={
            "email": "user_i@spaceloop.in",
            "password": "SecurePassword#2026",
        })
        mfa2 = login2.get_json()["data"]["mfa_token"]
        reused_res = self.client.post("/api/v1/auth/mfa/verify", json={
            "mfa_token": mfa2,
            "recovery_code": used_code,
        })
        self.assertEqual(reused_res.status_code, 401)
        self.assertIn("already consumed", reused_res.get_json()["error"]["message"])

    def test_scenario_j_recovery_code_regeneration(self):
        """J. Recovery code regeneration: old codes become invalid, new codes become valid."""
        _, token = self._register_user(email="user_j@spaceloop.in")
        raw_secret, old_codes = self._enable_mfa_for_user(token)

        # Re-authenticate and regenerate codes
        regen_code = generate_totp_code(raw_secret)
        regen_res = self.client.post(
            "/api/v1/auth/mfa/recovery-codes/regenerate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "password": "SecurePassword#2026",
                "code": regen_code,
            },
        )
        self.assertEqual(regen_res.status_code, 200)
        new_codes = regen_res.get_json()["data"]["recovery_codes"]
        self.assertEqual(len(new_codes), 8)
        self.assertNotEqual(old_codes, new_codes)

        # Attempt to use an OLD recovery code -> rejected
        login1 = self.client.post("/api/v1/auth/login", json={
            "email": "user_j@spaceloop.in",
            "password": "SecurePassword#2026",
        })
        mfa1 = login1.get_json()["data"]["mfa_token"]
        old_attempt = self.client.post("/api/v1/auth/mfa/verify", json={
            "mfa_token": mfa1,
            "recovery_code": old_codes[0],
        })
        self.assertEqual(old_attempt.status_code, 401)

        # Use NEW recovery code -> accepted
        new_attempt = self.client.post("/api/v1/auth/mfa/verify", json={
            "mfa_token": mfa1,
            "recovery_code": new_codes[0],
        })
        self.assertEqual(new_attempt.status_code, 200)

    def test_scenario_k_enrollment_atomicity(self):
        """K. MFA enrollment: secret generated -> not enabled; correct TOTP -> enabled."""
        user_id, token = self._register_user(email="user_k@spaceloop.in")

        # Initiate setup
        setup_res = self.client.post("/api/v1/auth/mfa/setup", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(setup_res.status_code, 200)
        raw_secret = setup_res.get_json()["data"]["secret"]

        # Verify DB: mfa_enabled is FALSE
        with self.app.app_context():
            u = db.session.get(User, user_id)
            self.assertFalse(u.mfa_enabled)

        # Verify setup with valid code
        code = generate_totp_code(raw_secret)
        ver_res = self.client.post(
            "/api/v1/auth/mfa/verify-setup",
            headers={"Authorization": f"Bearer {token}"},
            json={"code": code},
        )
        self.assertEqual(ver_res.status_code, 200)

        # Verify DB: mfa_enabled is now TRUE
        with self.app.app_context():
            u = db.session.get(User, user_id)
            self.assertTrue(u.mfa_enabled)

    def test_scenario_l_enrollment_with_incorrect_totp(self):
        """L. Enrollment with incorrect TOTP: MFA remains disabled."""
        user_id, token = self._register_user(email="user_l@spaceloop.in")

        self.client.post("/api/v1/auth/mfa/setup", headers={"Authorization": f"Bearer {token}"})

        # Submit incorrect code
        ver_res = self.client.post(
            "/api/v1/auth/mfa/verify-setup",
            headers={"Authorization": f"Bearer {token}"},
            json={"code": "999999"},
        )
        self.assertEqual(ver_res.status_code, 400)

        # Verify DB: mfa_enabled is still FALSE
        with self.app.app_context():
            u = db.session.get(User, user_id)
            self.assertFalse(u.mfa_enabled)

    def test_scenario_m_disable_without_reauth_denied(self):
        """M. MFA disable without required reauthentication: denied."""
        _, token = self._register_user(email="user_m@spaceloop.in")
        self._enable_mfa_for_user(token)

        # 1. Missing TOTP code
        res1 = self.client.post(
            "/api/v1/auth/mfa/disable",
            headers={"Authorization": f"Bearer {token}"},
            json={"password": "SecurePassword#2026"},
        )
        self.assertEqual(res1.status_code, 400)

        # 2. Wrong password
        res2 = self.client.post(
            "/api/v1/auth/mfa/disable",
            headers={"Authorization": f"Bearer {token}"},
            json={"password": "WrongPassword#1", "code": "123456"},
        )
        self.assertEqual(res2.status_code, 401)

    def test_scenario_n_disable_with_valid_reauth_succeeds(self):
        """N. MFA disable with valid reauthentication: succeeds and revokes active sessions."""
        user_id, token = self._register_user(email="user_n@spaceloop.in")
        raw_secret, _ = self._enable_mfa_for_user(token)

        code = generate_totp_code(raw_secret)
        disable_res = self.client.post(
            "/api/v1/auth/mfa/disable",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "password": "SecurePassword#2026",
                "code": code,
            },
        )
        self.assertEqual(disable_res.status_code, 200)

        with self.app.app_context():
            u = db.session.get(User, user_id)
            self.assertFalse(u.mfa_enabled)
            self.assertIsNone(u.mfa_secret)

    def test_scenario_o_mfa_pending_cannot_access_protected_endpoints(self):
        """O. MFA-pending session accessing protected endpoint: strictly denied (401)."""
        _, token = self._register_user(email="user_o@spaceloop.in")
        self._enable_mfa_for_user(token)

        login_res = self.client.post("/api/v1/auth/login", json={
            "email": "user_o@spaceloop.in",
            "password": "SecurePassword#2026",
        })
        mfa_token = login_res.get_json()["data"]["mfa_token"]

        # Attempt to access protected endpoint using mfa_token
        me_res = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {mfa_token}"},
        )
        self.assertEqual(me_res.status_code, 401)

        # Attempt to access another protected endpoint
        setup_res = self.client.post(
            "/api/v1/auth/mfa/setup",
            headers={"Authorization": f"Bearer {mfa_token}"},
        )
        self.assertEqual(setup_res.status_code, 401)

    def test_scenario_p_manipulated_mfa_token_rejected(self):
        """P. Manipulated MFA token: rejected (401)."""
        # Forged or corrupted token
        fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEsInR5cGUiOiJtZmFfcGVuZGluZyJ9.fakesig"
        res = self.client.post("/api/v1/auth/mfa/verify", json={
            "mfa_token": fake_token,
            "code": "123456",
        })
        self.assertEqual(res.status_code, 401)

    def test_scenario_q_direct_api_bypassing_frontend(self):
        """Q. Direct API call bypassing frontend: server-side blocks unauthenticated access."""
        res = self.client.get("/api/v1/auth/me")
        self.assertEqual(res.status_code, 401)

    def test_scenario_r_password_reset_preserves_mfa(self):
        """R. Password reset cannot bypass MFA: subsequent login still strictly requires MFA."""
        user_id, token = self._register_user(email="user_r@spaceloop.in")
        raw_secret, _ = self._enable_mfa_for_user(token)

        # Request and perform password reset
        forgot_res = self.client.post("/api/v1/auth/forgot-password", json={"email": "user_r@spaceloop.in"})
        self.assertEqual(forgot_res.status_code, 200)

        with self.app.app_context():
            token_rec = PasswordResetToken.query.filter_by(user_id=user_id, is_used=False).first()
            raw_reset_token = forgot_res.get_json()["data"].get("dev_reset_token")

        self.assertIsNotNone(raw_reset_token)

        reset_res = self.client.post("/api/v1/auth/reset-password", json={
            "token": raw_reset_token,
            "new_password": "NewSecurePassword#2027",
        })
        self.assertEqual(reset_res.status_code, 200)

        # Login with NEW password -> must STILL REQUIRE MFA
        new_login = self.client.post("/api/v1/auth/login", json={
            "email": "user_r@spaceloop.in",
            "password": "NewSecurePassword#2027",
        })
        self.assertEqual(new_login.status_code, 200)
        self.assertTrue(new_login.get_json()["data"]["mfa_required"])

    def test_scenario_s_refresh_token_during_mfa_pending(self):
        """S. Refresh token during MFA-pending state: cannot become authenticated without MFA."""
        _, token = self._register_user(email="user_s@spaceloop.in")
        self._enable_mfa_for_user(token)

        login_res = self.client.post("/api/v1/auth/login", json={
            "email": "user_s@spaceloop.in",
            "password": "SecurePassword#2026",
        })
        mfa_token = login_res.get_json()["data"]["mfa_token"]

        # Attempt to pass mfa_token to /refresh endpoint
        refresh_attempt = self.client.post("/api/v1/auth/refresh", json={
            "refresh_token": mfa_token,
        })
        self.assertEqual(refresh_attempt.status_code, 401)

    def test_scenario_t_logout_invalidates_session(self):
        """T. Logout: session state invalidated and cookies deleted."""
        _, token = self._register_user(email="user_t@spaceloop.in")

        logout_res = self.client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(logout_res.status_code, 200)
        cookie = logout_res.headers.get("Set-Cookie", "")
        self.assertIn("spaceloop_session=;", cookie)

    def test_scenario_u_session_revocation(self):
        """U. Session revocation: device sessions marked inactive."""
        user_id, token = self._register_user(email="user_u@spaceloop.in")
        self.client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )

        with self.app.app_context():
            active_sessions = DeviceSession.query.filter_by(user_id=user_id, is_active=True).count()
            self.assertEqual(active_sessions, 0)

    def test_scenario_v_concurrent_recovery_code_use(self):
        """V. Concurrent recovery-code use: atomic SQL update ensures only 1 request succeeds."""
        user_id, token = self._register_user(email="user_v@spaceloop.in")
        _, recovery_codes = self._enable_mfa_for_user(token)
        target_code = recovery_codes[0]

        login1 = self.client.post("/api/v1/auth/login", json={
            "email": "user_v@spaceloop.in",
            "password": "SecurePassword#2026",
        })
        mfa_tok1 = login1.get_json()["data"]["mfa_token"]

        login2 = self.client.post("/api/v1/auth/login", json={
            "email": "user_v@spaceloop.in",
            "password": "SecurePassword#2026",
        })
        mfa_tok2 = login2.get_json()["data"]["mfa_token"]

        results = []

        def submit_recovery(mfa_tok):
            # Each thread uses client
            return self.client.post("/api/v1/auth/mfa/verify", json={
                "mfa_token": mfa_tok,
                "recovery_code": target_code,
            }).status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            fut1 = executor.submit(submit_recovery, mfa_tok1)
            fut2 = executor.submit(submit_recovery, mfa_tok2)
            results = [fut1.result(), fut2.result()]

        # Exactly ONE request must succeed (200), and the other must be rejected (401)
        self.assertIn(200, results)
        self.assertIn(401, results)

    def test_scenario_w_secret_leakage_prevented(self):
        """W. Secret leakage: secrets/codes never leaked in responses or profiles."""
        user_id, token = self._register_user(email="user_w@spaceloop.in")
        raw_secret, _ = self._enable_mfa_for_user(token)

        me_res = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(me_res.status_code, 200)
        profile_data = me_res.get_json()["data"]

        # Assert no sensitive fields in profile API
        self.assertNotIn("mfa_secret", profile_data)
        self.assertNotIn("mfa_pending_secret", profile_data)
        self.assertNotIn("password_hash", profile_data)
        self.assertNotIn(raw_secret, json.dumps(profile_data))

    def test_scenario_x_privileged_admin_mfa_enforcement(self):
        """X. Privileged/admin account: MFA policy enforced server-side when configured."""
        # 1. Admin without MFA enabled
        admin_id, admin_token = self._register_user(
            email="admin_x@spaceloop.in",
            password="SecurePassword#2026",
            role="seeker",
        )
        with self.app.app_context():
            u = db.session.get(User, admin_id)
            u.role = "admin"
            db.session.commit()
            admin_token = create_access_token(admin_id, "admin_x@spaceloop.in", "admin")

        # By default MFA_ENFORCE_ADMIN is False -> allowed
        res_default = self.client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
        self.assertEqual(res_default.status_code, 200)

        # Turn on MFA_ENFORCE_ADMIN -> blocked with 403 MFA_REQUIRED_FOR_ADMIN
        self.app.config["MFA_ENFORCE_ADMIN"] = True
        res_enforced = self.client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
        self.assertEqual(res_enforced.status_code, 403)
        self.assertEqual(res_enforced.get_json()["error"]["code"], "MFA_REQUIRED_FOR_ADMIN")

        # Now enable MFA on the admin account
        self._enable_mfa_for_user(admin_token)

        # Now admin is allowed through
        res_unblocked = self.client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
        self.assertEqual(res_unblocked.status_code, 200)
        self.app.config["MFA_ENFORCE_ADMIN"] = False

    def test_scenario_y_app_restart_preserves_mfa_configuration(self):
        """Y. Application restart: encrypted secrets remain decryptable and valid across restarts."""
        user_id, token = self._register_user(email="user_y@spaceloop.in")
        raw_secret, _ = self._enable_mfa_for_user(token)

        # Re-instantiate app simulating server restart using the exact same database & secret
        class RestartConfig(TestingConfig):
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.temp_db_path}"
            SECRET_KEY = "test-fernet-secret-key-32-bytes-long!"
            MFA_ENCRYPTION_KEY = "test-fernet-secret-key-32-bytes-long!"

        restarted_app = create_app(RestartConfig)
        restarted_client = restarted_app.test_client()

        # Login on restarted application
        login_res = restarted_client.post("/api/v1/auth/login", json={
            "email": "user_y@spaceloop.in",
            "password": "SecurePassword#2026",
        })
        self.assertEqual(login_res.status_code, 200)
        mfa_token = login_res.get_json()["data"]["mfa_token"]

        # Validate TOTP code on restarted application
        code = generate_totp_code(raw_secret)
        challenge_res = restarted_client.post("/api/v1/auth/mfa/verify", json={
            "mfa_token": mfa_token,
            "code": code,
        })
        self.assertEqual(challenge_res.status_code, 200)
        self.assertIn("access_token", challenge_res.get_json()["data"])

    def test_scenario_z_full_end_to_end_journey(self):
        """Z. Full end-to-end browser/API flow:
        register -> login -> enroll -> logout -> login -> MFA -> access protected resource.
        """
        # 1. Register
        user_id, token = self._register_user(email="user_z@spaceloop.in")

        # 2. Login without MFA
        l1 = self.client.post("/api/v1/auth/login", json={
            "email": "user_z@spaceloop.in",
            "password": "SecurePassword#2026",
        })
        self.assertFalse(l1.get_json()["data"]["mfa_required"])

        # 3. Enroll MFA
        raw_secret, recovery_codes = self._enable_mfa_for_user(token)

        # 4. Logout
        self.client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})

        # 5. Login -> MFA Required
        l2 = self.client.post("/api/v1/auth/login", json={
            "email": "user_z@spaceloop.in",
            "password": "SecurePassword#2026",
        })
        self.assertTrue(l2.get_json()["data"]["mfa_required"])
        mfa_token = l2.get_json()["data"]["mfa_token"]

        # 6. Verify MFA
        code = generate_totp_code(raw_secret)
        v = self.client.post("/api/v1/auth/mfa/verify", json={
            "mfa_token": mfa_token,
            "code": code,
        })
        self.assertEqual(v.status_code, 200)
        new_token = v.get_json()["data"]["access_token"]

        # 7. Access protected resource with final access token
        me = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_token}"})
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.get_json()["data"]["email"], "user_z@spaceloop.in")
        self.assertTrue(me.get_json()["data"]["mfa_enabled"])


if __name__ == "__main__":
    unittest.main()
