-- schema.sql
-- 참고용 문서입니다. 실제 테이블 생성은 main.py의 init_db()에서
-- CREATE TABLE IF NOT EXISTS로 처리합니다 (이 파일을 코드가 읽지는 않습니다).

CREATE TABLE records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT NOT NULL,
    date TEXT NOT NULL,
    weight REAL NOT NULL,
    height REAL NOT NULL,
    systolic INTEGER NOT NULL,
    diastolic INTEGER NOT NULL,
    blood_sugar INTEGER NOT NULL,
    steps INTEGER DEFAULT 0,
    sleep_hours REAL DEFAULT 0.0,
    memo TEXT DEFAULT ''
);

CREATE INDEX idx_records_user ON records(user);
CREATE INDEX idx_records_date ON records(date);

CREATE TABLE goals (
    user TEXT PRIMARY KEY,
    target_weight REAL,
    target_systolic INTEGER,
    target_diastolic INTEGER
);
