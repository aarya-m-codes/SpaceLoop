"""Verification Service for SpaceLoop.

Coordinates:
- Student Enrollment Verification (15% discount, SHA-256 tokenization, zero raw ID storage)
- Aadhaar Tokenization & Validation (SHA-256, masked display, zero raw number storage)
- Host Physical & Financial Verification (DISCOM electricity connection + UPI penny-drop name matching)
- Clear delineation between development mock and live external verification
"""

import hashlib
import logging
import os
from typing import Any

from backend.core.database import db
from backend.modules.verification.adapters.aadhaar_adapter import (
    BaseAadhaarVerificationAdapter,
    MockAadhaarVerificationAdapter,
    ProductionAadhaarVerificationAdapter,
)
from backend.modules.verification.adapters.discom_adapter import (
    BaseDiscomVerificationAdapter,
    MockDiscomVerificationAdapter,
    ProductionDiscomVerificationAdapter,
)
from backend.modules.verification.adapters.student_adapter import (
    BaseStudentVerificationAdapter,
    MockStudentVerificationAdapter,
    ProductionStudentVerificationAdapter,
)
from backend.modules.verification.adapters.upi_adapter import (
    BaseUPIVerificationAdapter,
    MockUPIPennyDropAdapter,
    ProductionUPIPennyDropAdapter,
)
from models import User

logger = logging.getLogger("spaceloop.verification.service")


class VerificationService:
    """Core identity, host, and student verification orchestrator."""

    _student_adapter: BaseStudentVerificationAdapter | None = None
    _aadhaar_adapter: BaseAadhaarVerificationAdapter | None = None
    _discom_adapter: BaseDiscomVerificationAdapter | None = None
    _upi_adapter: BaseUPIVerificationAdapter | None = None

    # -------------------------------------------------------------------------
    # Adapter Resolvers
    # -------------------------------------------------------------------------

    @classmethod
    def get_student_adapter(cls) -> BaseStudentVerificationAdapter:
        if cls._student_adapter:
            return cls._student_adapter
        is_prod = os.getenv("FLASK_ENV") == "production" or os.getenv("ENV") == "production"
        return ProductionStudentVerificationAdapter() if is_prod else MockStudentVerificationAdapter()

    @classmethod
    def set_student_adapter(cls, adapter: BaseStudentVerificationAdapter | None) -> None:
        cls._student_adapter = adapter

    @classmethod
    def get_aadhaar_adapter(cls) -> BaseAadhaarVerificationAdapter:
        if cls._aadhaar_adapter:
            return cls._aadhaar_adapter
        is_prod = os.getenv("FLASK_ENV") == "production" or os.getenv("ENV") == "production"
        return ProductionAadhaarVerificationAdapter() if is_prod else MockAadhaarVerificationAdapter()

    @classmethod
    def set_aadhaar_adapter(cls, adapter: BaseAadhaarVerificationAdapter | None) -> None:
        cls._aadhaar_adapter = adapter

    @classmethod
    def get_discom_adapter(cls) -> BaseDiscomVerificationAdapter:
        if cls._discom_adapter:
            return cls._discom_adapter
        is_prod = os.getenv("FLASK_ENV") == "production" or os.getenv("ENV") == "production"
        return ProductionDiscomVerificationAdapter() if is_prod else MockDiscomVerificationAdapter()

    @classmethod
    def set_discom_adapter(cls, adapter: BaseDiscomVerificationAdapter | None) -> None:
        cls._discom_adapter = adapter

    @classmethod
    def get_upi_adapter(cls) -> BaseUPIVerificationAdapter:
        if cls._upi_adapter:
            return cls._upi_adapter
        is_prod = os.getenv("FLASK_ENV") == "production" or os.getenv("ENV") == "production"
        return ProductionUPIPennyDropAdapter() if is_prod else MockUPIPennyDropAdapter()

    @classmethod
    def set_upi_adapter(cls, adapter: BaseUPIVerificationAdapter | None) -> None:
        cls._upi_adapter = adapter

    # -------------------------------------------------------------------------
    # 1. Student Verification
    # -------------------------------------------------------------------------

    @classmethod
    def verify_student(
        cls,
        user_id: int | None,
        student_id: str,
        university_email: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Verify student status, grant 15% discount, and tokenize student ID via SHA-256."""
        clean_id = (student_id or "").strip()
        clean_email = (university_email or "").strip().lower()

        if not clean_id:
            raise ValueError("Student ID is required.")
        if not clean_email:
            raise ValueError("University email is required.")

        adapter = cls.get_student_adapter()
        result = adapter.verify_student(clean_id, clean_email, context)

        if not result.is_verified:
            return {
                "student_verified": False,
                "discount_rate": 0.0,
                "error": result.error or "Student verification failed.",
                "verification_mode": result.verification_mode,
                "external_verified": result.external_verified,
            }

        # Verification succeeded: apply to user record if user_id is provided
        if user_id:
            user = User.query.get(user_id)
            if user:
                user.is_student_verified = True
                user.student_discount_rate = result.discount_rate  # 0.15
                user.student_id_hash = result.student_id_hash
                user.university_email = clean_email
                db.session.commit()

        return {
            "student_verified": True,
            "discount_rate": result.discount_rate,  # 0.15 (15% discount rate)
            "student_id_token": result.student_id_hash,
            "university_email": clean_email,
            "institution_name": result.institution_name,
            "verification_mode": result.verification_mode,
            "external_verified": result.external_verified,
        }

    # -------------------------------------------------------------------------
    # 2. Aadhaar Verification
    # -------------------------------------------------------------------------

    @classmethod
    def verify_aadhaar(
        cls,
        user_id: int | None,
        raw_aadhaar: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Verify Indian Aadhaar, never storing the raw 12-digit number."""
        clean_aadhaar = (raw_aadhaar or "").strip()
        if not clean_aadhaar:
            raise ValueError("Aadhaar number is required.")

        adapter = cls.get_aadhaar_adapter()
        result = adapter.verify_aadhaar(clean_aadhaar, context)

        if not result.is_verified:
            return {
                "aadhaar_verified": False,
                "error": result.error or "Aadhaar verification failed.",
                "verification_mode": result.verification_mode,
                "external_verified": result.external_verified,
            }

        if user_id:
            user = User.query.get(user_id)
            if user:
                user.aadhaar_hash = result.aadhaar_hash
                user.kyc_status = "VERIFIED"
                user.is_verified = True
                db.session.commit()

        return {
            "aadhaar_verified": True,
            "masked_aadhaar": result.masked_aadhaar,
            "aadhaar_token": result.aadhaar_hash,
            "verification_mode": result.verification_mode,
            "external_verified": result.external_verified,
        }

    # -------------------------------------------------------------------------
    # 3. Host Verification (DISCOM + UPI Penny-Drop)
    # -------------------------------------------------------------------------

    @classmethod
    def verify_host(
        cls,
        user_id: int | None,
        discom_consumer_no: str,
        discom_provider: str,
        upi_vpa: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Verify host utility connection and UPI beneficiary matching."""
        clean_consumer = (discom_consumer_no or "").strip()
        clean_provider = (discom_provider or "").strip()
        clean_vpa = (upi_vpa or "").strip().lower()

        if not clean_consumer:
            raise ValueError("DISCOM consumer account number is required.")
        if not clean_provider:
            raise ValueError("DISCOM provider is required.")
        if not clean_vpa:
            raise ValueError("UPI VPA is required.")

        user = User.query.get(user_id) if user_id else None
        expected_name = user.full_name if user else "Host Property"

        # 1. DISCOM Verification
        discom_adapter = cls.get_discom_adapter()
        discom_res = discom_adapter.verify_discom_account(clean_consumer, clean_provider, context)

        if not discom_res.is_verified:
            return {
                "host_verified": False,
                "discom_verified": False,
                "upi_verified": False,
                "error": discom_res.error or "DISCOM electricity verification failed.",
                "verification_mode": discom_res.verification_mode,
                "external_verified": discom_res.external_verified,
            }

        # 2. UPI Penny-Drop & Name Matching
        upi_adapter = cls.get_upi_adapter()
        upi_res = upi_adapter.verify_vpa_and_name(clean_vpa, expected_name, context)

        if not upi_res.is_verified or not upi_res.is_name_match:
            err = upi_res.error or f"UPI beneficiary name '{upi_res.account_holder_name}' does not match registered host name '{expected_name}'."
            return {
                "host_verified": False,
                "discom_verified": True,
                "upi_verified": False,
                "error": err,
                "verification_mode": upi_res.verification_mode,
                "external_verified": upi_res.external_verified,
            }

        # Both passed -> update host record
        if user:
            user.is_host_verified = True
            user.discom_consumer_hash = discom_res.consumer_number_hash
            user.discom_provider = clean_provider
            user.upi_vpa = clean_vpa
            user.is_verified = True
            db.session.commit()

        external_verified = discom_res.external_verified and upi_res.external_verified
        verification_mode = "external_live" if external_verified else "mock"

        return {
            "host_verified": True,
            "discom_verified": True,
            "upi_verified": True,
            "discom_provider": clean_provider,
            "discom_consumer_token": discom_res.consumer_number_hash,
            "upi_vpa": clean_vpa,
            "account_holder_name": upi_res.account_holder_name,
            "name_match_score": upi_res.name_match_score,
            "verification_mode": verification_mode,
            "external_verified": external_verified,
        }
