-- Chạy file này trong Supabase SQL Editor

CREATE TABLE IF NOT EXISTS ocr_sessions (
    id         BIGSERIAL PRIMARY KEY,
    username   TEXT NOT NULL,
    image_key  TEXT NOT NULL,
    image_name TEXT DEFAULT '',
    doc_name   TEXT DEFAULT '',
    num_boxes  INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(username, image_key)
);

CREATE TABLE IF NOT EXISTS ocr_boxes (
    id            BIGSERIAL PRIMARY KEY,
    session_id    BIGINT NOT NULL REFERENCES ocr_sessions(id) ON DELETE CASCADE,
    box_index     INTEGER NOT NULL,
    nom_ocr       TEXT DEFAULT '',
    nom_corrected TEXT DEFAULT NULL,
    hanviet       TEXT DEFAULT '',
    accuracy      TEXT DEFAULT '',
    saved         BOOLEAN DEFAULT FALSE,
    updated_at    TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(session_id, box_index)
);

-- Dùng service_role key nên tắt RLS cho đơn giản
ALTER TABLE ocr_sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE ocr_boxes DISABLE ROW LEVEL SECURITY;
