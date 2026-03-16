-- InsForge Schema for Random Tactical Timer
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_training_cycles INT DEFAULT 0
);

CREATE TABLE training_cycles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    min_time_sec INT NOT NULL,
    max_time_sec INT NOT NULL,
    actual_time_sec INT NOT NULL,
    reaction_time_ms INT, 
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for WQTU calculation (Weekly Qualified Training Users)
CREATE INDEX idx_training_cycles_user_id_created_at ON training_cycles(user_id, created_at);
