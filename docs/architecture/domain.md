# Domain Model & Ubiquitous Language

## Key Entities
- **User**: Marketplace actor with roles (seeker, host, admin), KYC/verification tier, and trust score.
- **Space**: Physical listing with coordinates, daily/hourly rates, capacity, rules, and host ownership.
- **Booking**: Temporal reservation lifecycle (requested, confirmed, checked_in, checked_out, completed, cancelled, disputed).
- **EscrowTransaction**: Double-entry financial hold storing subtotal, 5% fee, and ₹100 refundable deposit.
- **AccessLog**: GPS coordinates, timestamp, method (QR / PIN), and verification status.
