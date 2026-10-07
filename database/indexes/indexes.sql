-- SpaceLoop Query Optimization Indexes

CREATE INDEX IF NOT EXISTS idx_spaces_city ON spaces (city);
CREATE INDEX IF NOT EXISTS idx_spaces_type ON spaces (space_type);
CREATE INDEX IF NOT EXISTS idx_spaces_rate ON spaces (hourly_rate);
CREATE INDEX IF NOT EXISTS idx_spaces_host ON spaces (host_id);
CREATE INDEX IF NOT EXISTS idx_bookings_seeker ON bookings (seeker_id);
CREATE INDEX IF NOT EXISTS idx_bookings_space ON bookings (space_id);
CREATE INDEX IF NOT EXISTS idx_bookings_times ON bookings (start_time, end_time);
CREATE INDEX IF NOT EXISTS idx_escrows_status ON escrows (status);
