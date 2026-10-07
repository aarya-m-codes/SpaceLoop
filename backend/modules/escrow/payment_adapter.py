"""Payment adapter interface and deterministic mock implementation for SpaceLoop financial escrow.

Provides a pluggable abstraction layer for UPI collections, disbursements, and penny-drop validations.
In development mode, uses deterministic simulations that never claim real payments occurred.
"""

import logging
import re
import secrets
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any

logger = logging.getLogger("spaceloop.escrow.payment")

# Standard NPCI UPI Virtual Payment Address (VPA) regex validation: e.g. user@bank, 9876543210@paytm
UPI_VPA_REGEX = re.compile(r"^[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}$")


@dataclass
class PaymentResult:
    """Standardized payment transaction outcome payload."""
    success: bool
    transaction_id: str
    reference_id: str
    amount: float
    currency: str
    status: str  # "pending", "completed", "failed"
    is_mock: bool
    mock_disclaimer: str | None
    payer_vpa: str | None = None
    payee_vpa: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PennyDropResult:
    """Standardized penny-drop bank account verification outcome."""
    is_valid: bool
    vpa: str
    account_holder_name: str | None
    reference_id: str
    amount: float
    is_mock: bool
    mock_disclaimer: str
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BasePaymentAdapter(ABC):
    """Abstract payment adapter interface to be implemented by real UPI gateways or test mocks."""

    @property
    @abstractmethod
    def is_mock(self) -> bool:
        """Indicates whether this adapter operates in simulated development mode."""
        pass

    @abstractmethod
    def validate_vpa(self, vpa: str) -> bool:
        """Validate UPI Virtual Payment Address format."""
        pass

    @abstractmethod
    def initiate_collection(
        self,
        amount: float,
        payer_vpa: str,
        reference_id: str,
        description: str = "",
    ) -> PaymentResult:
        """Initiate or simulate an inbound payment collection (debit from seeker)."""
        pass

    @abstractmethod
    def execute_payout(
        self,
        amount: float,
        payee_vpa: str,
        reference_id: str,
        description: str = "",
    ) -> PaymentResult:
        """Initiate or simulate an outbound payout (credit to host or seeker refund)."""
        pass

    @abstractmethod
    def verify_penny_drop(self, vpa: str) -> PennyDropResult:
        """Execute ₹1.00 penny-drop account name verification before disbursement."""
        pass


class MockUPIPaymentAdapter(BasePaymentAdapter):
    """Deterministic development/testing UPI payment adapter.

    CRITICAL RULE: Never claims a real payment occurred; explicitly marks every
    transaction with is_mock=True and provides a clear mock disclaimer.
    """

    MOCK_DISCLAIMER = "DEVELOPMENT SIMULATION: No real currency was debited or credited."

    @property
    def is_mock(self) -> bool:
        return True

    def validate_vpa(self, vpa: str) -> bool:
        """Check standard UPI VPA syntax."""
        if not vpa or not isinstance(vpa, str):
            return False
        return bool(UPI_VPA_REGEX.match(vpa.strip()))

    def initiate_collection(
        self,
        amount: float,
        payer_vpa: str,
        reference_id: str,
        description: str = "",
    ) -> PaymentResult:
        """Simulate deterministic UPI collection from seeker."""
        if amount <= 0:
            raise ValueError(f"Collection amount must be strictly greater than zero (got {amount}).")

        clean_vpa = (payer_vpa or "").strip()
        if clean_vpa and not self.validate_vpa(clean_vpa):
            raise ValueError(f"Invalid UPI VPA format: '{clean_vpa}'. Expected user@bank.")

        txn_id = f"MOCK-UPI-COLL-{secrets.token_hex(6).upper()}"
        logger.info(
            f"[MOCK PAYMENT] Inbound collection: ₹{amount:.2f} from {clean_vpa or 'seeker'} "
            f"(Ref: {reference_id}) [{self.MOCK_DISCLAIMER}]"
        )

        return PaymentResult(
            success=True,
            transaction_id=txn_id,
            reference_id=reference_id,
            amount=round(amount, 2),
            currency="INR",
            status="completed",
            is_mock=True,
            mock_disclaimer=self.MOCK_DISCLAIMER,
            payer_vpa=clean_vpa or "seeker.test@okhdfcbank",
            error_message=None,
        )

    def execute_payout(
        self,
        amount: float,
        payee_vpa: str,
        reference_id: str,
        description: str = "",
    ) -> PaymentResult:
        """Simulate deterministic UPI payout to host or refund to seeker."""
        if amount <= 0:
            raise ValueError(f"Payout amount must be strictly greater than zero (got {amount}).")

        clean_vpa = (payee_vpa or "").strip()
        if clean_vpa and not self.validate_vpa(clean_vpa):
            raise ValueError(f"Invalid UPI VPA format: '{clean_vpa}'. Expected user@bank.")

        txn_id = f"MOCK-UPI-PAYOUT-{secrets.token_hex(6).upper()}"
        logger.info(
            f"[MOCK PAYMENT] Outbound payout: ₹{amount:.2f} to {clean_vpa or 'payee'} "
            f"(Ref: {reference_id}) [{self.MOCK_DISCLAIMER}]"
        )

        return PaymentResult(
            success=True,
            transaction_id=txn_id,
            reference_id=reference_id,
            amount=round(amount, 2),
            currency="INR",
            status="completed",
            is_mock=True,
            mock_disclaimer=self.MOCK_DISCLAIMER,
            payee_vpa=clean_vpa or "host.test@okaxis",
            error_message=None,
        )

    def verify_penny_drop(self, vpa: str) -> PennyDropResult:
        """Simulate ₹1.00 penny-drop account holder verification."""
        clean_vpa = (vpa or "").strip()
        if not self.validate_vpa(clean_vpa):
            return PennyDropResult(
                is_valid=False,
                vpa=clean_vpa,
                account_holder_name=None,
                reference_id=f"PENNY-FAIL-{secrets.token_hex(4).upper()}",
                amount=1.00,
                is_mock=True,
                mock_disclaimer=self.MOCK_DISCLAIMER,
                error_message="Invalid UPI VPA syntax.",
            )

        # Derive account holder display name from VPA prefix
        user_part = clean_vpa.split("@")[0].replace(".", " ").replace("_", " ").title()
        ref_id = f"MOCK-PENNY-{secrets.token_hex(6).upper()}"

        return PennyDropResult(
            is_valid=True,
            vpa=clean_vpa,
            account_holder_name=f"{user_part} (Simulated Bank Verification)",
            reference_id=ref_id,
            amount=1.00,
            is_mock=True,
            mock_disclaimer=self.MOCK_DISCLAIMER,
            error_message=None,
        )


_default_adapter = MockUPIPaymentAdapter()


def get_payment_adapter() -> BasePaymentAdapter:
    """Return the active payment adapter instance."""
    return _default_adapter
