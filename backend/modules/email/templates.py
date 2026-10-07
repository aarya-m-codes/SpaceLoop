"""Transactional Email Templates for SpaceLoop Marketplace.

Generates HTML and plain-text renderings for:
1. verification (Email Verification)
2. password_reset (Password Reset Token)
3. booking (Reservation Confirmation)
4. cancellation (Cancellation & Refund Breakdown)
5. host_approval (Host Acceptance)
6. host_rejection (Host Rejection & 100% Refund)
7. check_in (Physical Access & Arrival Confirmation)
8. checkout (Session Completion & Deposit Release)
9. dispute (Dispute Notice & Escrow Freeze)
"""

from typing import Any


def _base_html_layout(title: str, content: str) -> str:
    """Standard responsive SpaceLoop branded HTML email shell."""
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #1e293b; margin: 0; padding: 24px; }}
    .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; }}
    .header {{ background: #0f172a; padding: 24px; text-align: center; color: #ffffff; }}
    .header h1 {{ margin: 0; font-size: 22px; font-weight: 700; letter-spacing: -0.5px; }}
    .body {{ padding: 32px 24px; line-height: 1.6; font-size: 15px; }}
    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 9999px; font-size: 13px; font-weight: 600; background: #e0f2fe; color: #0369a1; }}
    .card {{ background: #f1f5f9; border-radius: 8px; padding: 16px; margin: 20px 0; }}
    .pin {{ font-size: 28px; font-weight: 800; letter-spacing: 4px; color: #0284c7; text-align: center; margin: 12px 0; }}
    .footer {{ background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 20px; text-align: center; font-size: 12px; color: #64748b; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>SpaceLoop</h1>
    </div>
    <div class="body">
      {content}
    </div>
    <div class="footer">
      <p>&copy; 2026 SpaceLoop India. Peer-to-peer physical workspace & creative space marketplace.</p>
    </div>
  </div>
</body>
</html>"""


def render_email_template(template_name: str, data: dict[str, Any]) -> tuple[str, str, str]:
    """Render transactional email.

    Returns:
        (subject, html_content, text_content)
    """
    t_name = template_name.lower().strip()

    # 1. Verification
    if t_name == "verification":
        name = data.get("user_name") or "SpaceLoop Member"
        token = data.get("token", "123456")
        link = data.get("verify_url", f"https://spaceloop.in/verify-email?token={token}")
        subject = "Verify your SpaceLoop Account"
        content = f"""
        <h2>Welcome to SpaceLoop, {name}!</h2>
        <p>Please verify your email address to activate all marketplace features, including physical workspace bookings and host listings.</p>
        <div class="card" style="text-align: center;">
          <p style="margin: 0; font-weight: 600;">Your Verification Token:</p>
          <div class="pin">{token}</div>
          <p style="margin: 0;"><a href="{link}" style="color: #0284c7; text-decoration: underline;">Click here to automatically verify</a></p>
        </div>
        <p>This verification link expires in 24 hours.</p>
        """
        text = f"Welcome to SpaceLoop, {name}!\n\nVerify your account using token: {token}\nLink: {link}"
        return subject, _base_html_layout(subject, content), text

    # 2. Password Reset
    elif t_name == "password_reset":
        name = data.get("user_name") or "SpaceLoop Member"
        token = data.get("token", "")
        link = data.get("reset_url", f"https://spaceloop.in/reset-password?token={token}")
        subject = "Reset your SpaceLoop Password"
        content = f"""
        <h2>Password Reset Request</h2>
        <p>Hello {name}, we received a request to reset the password for your SpaceLoop account.</p>
        <div class="card" style="text-align: center;">
          <a href="{link}" style="display: inline-block; background: #0284c7; color: #ffffff; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 600;">Reset Password</a>
          <p style="margin-top: 12px; font-size: 13px; color: #64748b;">Or use reset token: <code>{token}</code></p>
        </div>
        <p>If you did not make this request, you can safely ignore this email.</p>
        """
        text = f"Reset your SpaceLoop password:\n{link}\nToken: {token}"
        return subject, _base_html_layout(subject, content), text

    # 3. Booking Confirmation
    elif t_name == "booking":
        space_name = data.get("space_title", "Workspace")
        start = data.get("start_time", "")
        end = data.get("end_time", "")
        pin = data.get("arrival_pin", "0000")
        total = data.get("total_price", 0.0)
        subject = f"Booking Confirmed: {space_name}"
        content = f"""
        <h2>Your Space is Reserved!</h2>
        <p>Your booking for <strong>{space_name}</strong> is confirmed.</p>
        <div class="card">
          <p><strong>Time Window:</strong> {start} &ndash; {end}</p>
          <p><strong>Total Amount Paid:</strong> &#8377;{total:.2f} (includes &#8377;100 refundable security deposit)</p>
          <hr style="border: 0; border-top: 1px solid #cbd5e1; margin: 16px 0;">
          <p style="margin: 0; font-weight: 600; text-align: center;">Your 4-Digit Arrival Access PIN:</p>
          <div class="pin">{pin}</div>
          <p style="font-size: 13px; color: #64748b; text-align: center; margin: 0;">Present this PIN at the door to unlock physical access once within the 50m geofence.</p>
        </div>
        """
        text = f"Booking Confirmed for {space_name}\nTime: {start} - {end}\nPIN: {pin}\nTotal: Rs. {total}"
        return subject, _base_html_layout(subject, content), text

    # 4. Cancellation
    elif t_name == "cancellation":
        booking_id = data.get("booking_id", "")
        refund_amount = data.get("refund_amount", 0.0)
        platform_fee = data.get("platform_fee", 0.0)
        deposit_refunded = data.get("deposit_refunded", 100.0)
        subject = f"Booking #{booking_id} Cancelled"
        content = f"""
        <h2>Booking Cancellation Notice</h2>
        <p>Your booking #{booking_id} has been cancelled per your request.</p>
        <div class="card">
          <p><strong>Refund Summary:</strong></p>
          <ul style="padding-left: 20px;">
            <li>100% Space Rental Subtotal: Refunded</li>
            <li>100% Security Deposit (&#8377;{deposit_refunded:.2f}): Released back to you</li>
            <li>Platform Fee (5% retained): &#8377;{platform_fee:.2f}</li>
          </ul>
          <p><strong>Total Refund Dispatched:</strong> &#8377;{refund_amount:.2f}</p>
        </div>
        <p>Your refund has been initiated to your original payment method.</p>
        """
        text = f"Booking #{booking_id} Cancelled.\nTotal refund: Rs. {refund_amount:.2f} (includes Rs. {deposit_refunded} deposit; Rs. {platform_fee} retained)."
        return subject, _base_html_layout(subject, content), text

    # 5. Host Approval
    elif t_name in ("host_approval", "approval"):
        space_name = data.get("space_title", "Workspace")
        booking_id = data.get("booking_id", "")
        pin = data.get("arrival_pin", "")
        subject = f"Host Accepted: {space_name}"
        content = f"""
        <h2>Good news! The host accepted your booking</h2>
        <p>Your reservation #{booking_id} at <strong>{space_name}</strong> was approved by the host.</p>
        {f'<div class="card"><p style="text-align: center; margin: 0;">Arrival PIN: <strong class="pin">{pin}</strong></p></div>' if pin else ''}
        <p>You can check in on your arrival date by entering your 4-digit arrival PIN at the entrance.</p>
        """
        text = f"Host accepted your booking #{booking_id} at {space_name}."
        return subject, _base_html_layout(subject, content), text

    # 6. Host Rejection
    elif t_name in ("host_rejection", "rejection"):
        space_name = data.get("space_title", "Workspace")
        booking_id = data.get("booking_id", "")
        refund_amount = data.get("refund_amount", 0.0)
        reason = data.get("reason", "Host unavailable for requested slot")
        subject = f"Host Declined: Booking #{booking_id}"
        content = f"""
        <h2>Booking Request Declined</h2>
        <p>The host was unable to accept your reservation #{booking_id} for <strong>{space_name}</strong>.</p>
        <div class="card">
          <p><strong>Reason:</strong> {reason}</p>
          <p><strong>100% Full Refund:</strong> &#8377;{refund_amount:.2f} has been credited back to your account with zero deductions.</p>
        </div>
        <p>Feel free to browse other verified workspaces in the area.</p>
        """
        text = f"Booking #{booking_id} was declined. 100% refund of Rs. {refund_amount:.2f} credited."
        return subject, _base_html_layout(subject, content), text

    # 7. Check-In
    elif t_name in ("check_in", "checkin"):
        space_name = data.get("space_title", "Workspace")
        booking_id = data.get("booking_id", "")
        check_in_time = data.get("check_in_time", "")
        subject = f"Checked In: {space_name}"
        content = f"""
        <h2>Check-in Verified!</h2>
        <p>You have successfully checked into <strong>{space_name}</strong> (Booking #{booking_id}).</p>
        <div class="card">
          <p><strong>Check-in Time:</strong> {check_in_time}</p>
          <p><strong>Geofence:</strong> 50m GPS verified</p>
          <p><strong>Inspection Photos:</strong> Uploaded and recorded to immutable ledger</p>
        </div>
        <p>Enjoy your session! Remember to submit check-out photos at departure to release your &#8377;100 deposit.</p>
        """
        text = f"Check-in verified at {space_name} (Booking #{booking_id}) at {check_in_time}."
        return subject, _base_html_layout(subject, content), text

    # 8. Check-Out
    elif t_name in ("checkout", "check_out"):
        space_name = data.get("space_title", "Workspace")
        booking_id = data.get("booking_id", "")
        deposit_released = data.get("deposit_released", 100.0)
        subject = f"Session Complete: {space_name}"
        content = f"""
        <h2>Check-out Complete</h2>
        <p>Thank you for using SpaceLoop! Your session at <strong>{space_name}</strong> (Booking #{booking_id}) is closed.</p>
        <div class="card">
          <p><strong>&#8377;{deposit_released:.2f} Security Deposit:</strong> Successfully released back to your account.</p>
          <p><strong>Space Condition:</strong> Verified via departure photos.</p>
        </div>
        <p>We invite you to leave a verified review to help our peer community.</p>
        """
        text = f"Check-out complete for {space_name}. Rs. {deposit_released:.2f} deposit released."
        return subject, _base_html_layout(subject, content), text

    # 9. Dispute
    elif t_name == "dispute":
        booking_id = data.get("booking_id", "")
        reason = data.get("dispute_reason", "Dispute raised")
        subject = f"Dispute Alert: Booking #{booking_id}"
        content = f"""
        <h2>Escrow Hold: Dispute Opened</h2>
        <p>A dispute has been submitted regarding Booking #{booking_id}.</p>
        <div class="card">
          <p><strong>Reason:</strong> {reason}</p>
          <p><strong>Escrow Status:</strong> All payout releases have been frozen pending Trust & Safety adjudication.</p>
        </div>
        <p>Our compliance team will review GPS telemetry, inspection photos, and door access timestamps.</p>
        """
        text = f"Dispute opened for Booking #{booking_id}. Reason: {reason}. Escrow frozen."
        return subject, _base_html_layout(subject, content), text

    # Default fallback
    else:
        subject = data.get("subject", "SpaceLoop Notification")
        body_text = data.get("message", "You have a new notification from SpaceLoop.")
        content = f"<h2>SpaceLoop Notice</h2><p>{body_text}</p>"
        return subject, _base_html_layout(subject, content), body_text
