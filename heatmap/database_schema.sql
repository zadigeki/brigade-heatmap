-- Database schema for Brigade Electronics devices
CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    car_license VARCHAR(50) NOT NULL,
    terid VARCHAR(50) UNIQUE NOT NULL,
    sim VARCHAR(20),
    channel INTEGER,
    plate_color INTEGER,
    group_id INTEGER,
    cname TEXT,
    device_type VARCHAR(10),
    link_type VARCHAR(10),
    device_username VARCHAR(50),
    device_password VARCHAR(50),
    register_ip VARCHAR(15),
    register_port INTEGER,
    transmit_ip VARCHAR(15),
    transmit_port INTEGER,
    channel_enable INTEGER,
    company_branch VARCHAR(100),
    company_name VARCHAR(100),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_devices_terid ON devices(terid);
CREATE INDEX IF NOT EXISTS idx_devices_car_license ON devices(car_license);
CREATE INDEX IF NOT EXISTS idx_devices_last_updated ON devices(last_updated);

-- Alarms table for storing alarm detail information
CREATE TABLE IF NOT EXISTS alarms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    terid VARCHAR(50) NOT NULL,
    gps_time TIMESTAMP,
    altitude INTEGER,
    direction INTEGER,
    gps_lat DECIMAL(10, 8),
    gps_lng DECIMAL(11, 8),
    speed INTEGER,
    record_speed INTEGER,
    state INTEGER,
    server_time TIMESTAMP,
    alarm_type INTEGER,
    alarm_content TEXT,
    cmd_type INTEGER,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (terid) REFERENCES devices(terid)
);

-- Indexes for alarms table
CREATE INDEX IF NOT EXISTS idx_alarms_terid ON alarms(terid);
CREATE INDEX IF NOT EXISTS idx_alarms_gps_time ON alarms(gps_time);
CREATE INDEX IF NOT EXISTS idx_alarms_alarm_type ON alarms(alarm_type);
CREATE INDEX IF NOT EXISTS idx_alarms_last_updated ON alarms(last_updated);
CREATE INDEX IF NOT EXISTS idx_alarms_created_at ON alarms(created_at);

-- Unique constraint to prevent duplicate alarms
-- Same device, GPS time, alarm type, and server time should not be duplicated
CREATE UNIQUE INDEX IF NOT EXISTS idx_alarms_unique ON alarms(terid, gps_time, alarm_type, server_time);