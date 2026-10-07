# Data Protection & Privacy Policy

## 1. Data Classification
- **Public**: Space listings, public reviews, photos, city-level geo-coordinates.
- **Internal**: Aggregated search analytics, platform commission rates.
- **Confidential**: User phone numbers, email addresses, booking receipts.
- **Restricted**: Payment tokens, smart lock master keys, Aadhaar/Government ID verification hashes.

## 2. Encryption
- **In Transit**: All HTTP connections strictly upgraded to TLS 1.3.
- **At Rest**: AES-256 encryption on database volumes and object storage buckets.
- **Credentials**: Passwords hashed using Bcrypt with work factor >= 12. Smart door PINs dynamically generated with time-bounded expiration.
