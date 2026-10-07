-- SpaceLoop Initial Seed Data

INSERT INTO users (id, email, password_hash, full_name, role, is_verified, trust_score)
VALUES 
('11111111-1111-1111-1111-111111111111', 'demo.seeker@spaceloop.io', 'pbkdf2:sha256:mock_hash', 'Aarya Merchant', 'seeker', true, 94.50),
('22222222-2222-2222-2222-222222222222', 'demo.host@spaceloop.io', 'pbkdf2:sha256:mock_hash', 'Vikramaditya Spaces', 'host', true, 98.20),
('33333333-3333-3333-3333-333333333333', 'admin@spaceloop.io', 'pbkdf2:sha256:mock_hash', 'SpaceLoop Trust & Safety', 'admin', true, 100.00)
ON CONFLICT (id) DO NOTHING;

INSERT INTO spaces (id, host_id, title, description, space_type, hourly_rate, address, city, amenities, is_verified, verification_level)
VALUES
('aaaaaaa1-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '22222222-2222-2222-2222-222222222222', 'The Skyline Architectural Studio', 'Panoramic skyline views, 1Gbps fiber optic line, and smart acoustic insulation.', 'studio', 850.00, 'Connaught Place, Central Delhi', 'New Delhi', '["WiFi 1Gbps", "Espresso Bar", "Smart Lock", "Soundproofing"]'::jsonb, true, 'PHYSICAL_INSPECTED'),
('aaaaaaa2-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '22222222-2222-2222-2222-222222222222', 'Silicon Hub Executive Desk', 'Private standing desk in top-tier tech incubator with ergonomic Herman Miller chair.', 'coworking', 350.00, 'Koramangala 4th Block', 'Bangalore', '["Ergonomic Chair", "Gigabit Internet", "Power Backup", "Conference Access"]'::jsonb, true, 'BASIC')
ON CONFLICT (id) DO NOTHING;
