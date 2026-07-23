import sqlite3
from datetime import date, timedelta

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import HTMLResponse

from fastapi.staticfiles import StaticFiles

app = FastAPI(title="마이 헬스 로그 API", version="1.0")

app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------- 데이터 모델 ----------

class RecordIn(BaseModel):
    user: str
    date: str
    weight: float
    height: float
    systolic: int
    diastolic: int
    blood_sugar: int
    steps: int = 0
    sleep_hours: float = 0.0
    memo: str = ""


class GoalIn(BaseModel):
    user: str
    target_weight: float | None = None
    target_systolic: int | None = None
    target_diastolic: int | None = None


# ---------- SQLite 초기화 ----------
# 실제 테이블 정의는 schema.sql(참고용)을 그대로 옮긴 것이다.

DB_FILE = "health.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS records (
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
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_records_user ON records(user)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_records_date ON records(date)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                user TEXT PRIMARY KEY,
                target_weight REAL,
                target_systolic INTEGER,
                target_diastolic INTEGER
            )
        """)
        conn.commit()
    finally:
        conn.close()


init_db()  # 서버 시작 시 한 번 호출


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


# ---------- 헬스케어 계산 로직 ----------

def calculate_bmi(weight: float, height: float) -> float:
    height_m = height / 100
    return round(weight / (height_m ** 2), 1)


def classify_bmi(bmi: float) -> str:
    if bmi < 18.5:
        return "저체중"
    elif bmi < 23:
        return "정상"
    elif bmi < 25:
        return "과체중"
    else:
        return "비만"


def classify_bp(systolic: int, diastolic: int) -> str:
    if systolic >= 140 or diastolic >= 90:
        return "고혈압"
    elif systolic >= 120 or diastolic >= 80:
        return "주의"
    else:
        return "정상"


def classify_sugar(blood_sugar: int) -> str:
    if blood_sugar >= 126:
        return "당뇨 의심"
    elif blood_sugar >= 100:
        return "공복혈당장애"
    else:
        return "정상"


def classify_steps(steps: int) -> str:
    if steps < 5000:
        return "부족"
    elif steps < 10000:
        return "적정"
    else:
        return "우수"


def classify_sleep(sleep_hours: float) -> str:
    if sleep_hours < 6:
        return "부족"
    elif sleep_hours <= 9:
        return "적정"
    else:
        return "과다"


def generate_warnings(bmi_category: str, bp_category: str, sugar_category: str) -> list[str]:
    warnings = []
    if bmi_category == "비만":
        warnings.append("BMI가 비만 범위입니다.")
    if bp_category == "고혈압":
        warnings.append("혈압이 고혈압 범위입니다.")
    if sugar_category == "당뇨 의심":
        warnings.append("혈당이 당뇨 의심 범위입니다.")
    return warnings


def enrich(record: dict) -> dict:
    """저장된 원본 기록에 계산 필드를 붙여서 반환"""
    bmi = calculate_bmi(record["weight"], record["height"])
    bmi_category = classify_bmi(bmi)
    bp_category = classify_bp(record["systolic"], record["diastolic"])
    sugar_category = classify_sugar(record["blood_sugar"])

    return {
        **record,
        "bmi": bmi,
        "bmi_category": bmi_category,
        "bp_category": bp_category,
        "sugar_category": sugar_category,
        "steps_grade": classify_steps(record["steps"]),
        "sleep_category": classify_sleep(record["sleep_hours"]),
        "warnings": generate_warnings(bmi_category, bp_category, sugar_category),
    }


# ---------- 기본 ----------

@app.get("/")
def read_root():
    return {"message": "마이 헬스 로그 API"}


# ---------- 기록 CRUD ----------

@app.post("/records")
def create_record(record: RecordIn):
    data = record.model_dump()
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            INSERT INTO records
                (user, date, weight, height, systolic, diastolic, blood_sugar, steps, sleep_hours, memo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["user"], data["date"], data["weight"], data["height"],
                data["systolic"], data["diastolic"], data["blood_sugar"],
                data["steps"], data["sleep_hours"], data["memo"],
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM records WHERE id = ?", (cur.lastrowid,)).fetchone()
        return enrich(dict(row))
    finally:
        conn.close()


@app.get("/records")
def list_records(user: str | None = None):
    conn = get_conn()
    try:
        if user is not None:
            rows = conn.execute("SELECT * FROM records WHERE user = ?", (user,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM records").fetchall()
        target = [dict(r) for r in rows]
        return {"count": len(target), "records": [enrich(r) for r in target]}
    finally:
        conn.close()


@app.get("/records/{record_id}")
def get_record(record_id: int):
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM records WHERE id = ?", (record_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="record not found")
        return enrich(dict(row))
    finally:
        conn.close()


@app.put("/records/{record_id}")
def update_record(record_id: int, record: RecordIn):
    data = record.model_dump()
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            UPDATE records
            SET user = ?, date = ?, weight = ?, height = ?, systolic = ?,
                diastolic = ?, blood_sugar = ?, steps = ?, sleep_hours = ?, memo = ?
            WHERE id = ?
            """,
            (
                data["user"], data["date"], data["weight"], data["height"],
                data["systolic"], data["diastolic"], data["blood_sugar"],
                data["steps"], data["sleep_hours"], data["memo"], record_id,
            ),
        )
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="record not found")
        row = conn.execute("SELECT * FROM records WHERE id = ?", (record_id,)).fetchone()
        return enrich(dict(row))
    finally:
        conn.close()


@app.delete("/records/{record_id}")
def delete_record(record_id: int):
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM records WHERE id = ?", (record_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="record not found")
        conn.execute("DELETE FROM records WHERE id = ?", (record_id,))
        conn.commit()
        return {"deleted": enrich(dict(row))}
    finally:
        conn.close()


# ---------- 검색 · 통계 · 주간 리포트 ----------

@app.get("/search")
def search_records(start: str, end: str, user: str | None = None):
    conn = get_conn()
    try:
        if user is not None:
            rows = conn.execute(
                "SELECT * FROM records WHERE date BETWEEN ? AND ? AND user = ?",
                (start, end, user),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM records WHERE date BETWEEN ? AND ?",
                (start, end),
            ).fetchall()
        filtered = [dict(r) for r in rows]
        return {"count": len(filtered), "records": [enrich(r) for r in filtered]}
    finally:
        conn.close()


@app.get("/stats")
def get_stats(user: str | None = None):
    conn = get_conn()
    try:
        if user is not None:
            row = conn.execute(
                """
                SELECT COUNT(*) AS count, AVG(weight) AS avg_weight, AVG(systolic) AS avg_systolic,
                       AVG(diastolic) AS avg_diastolic, AVG(blood_sugar) AS avg_blood_sugar,
                       AVG(steps) AS avg_steps, AVG(sleep_hours) AS avg_sleep_hours
                FROM records WHERE user = ?
                """,
                (user,),
            ).fetchone()
        else:
            row = conn.execute(
                """
                SELECT COUNT(*) AS count, AVG(weight) AS avg_weight, AVG(systolic) AS avg_systolic,
                       AVG(diastolic) AS avg_diastolic, AVG(blood_sugar) AS avg_blood_sugar,
                       AVG(steps) AS avg_steps, AVG(sleep_hours) AS avg_sleep_hours
                FROM records
                """
            ).fetchone()

        if row["count"] == 0:
            return {"count": 0}

        return {
            "count": row["count"],
            "avg_weight": round(row["avg_weight"], 1),
            "avg_systolic": round(row["avg_systolic"], 1),
            "avg_diastolic": round(row["avg_diastolic"], 1),
            "avg_blood_sugar": round(row["avg_blood_sugar"], 1),
            "avg_steps": round(row["avg_steps"], 1),
            "avg_sleep_hours": round(row["avg_sleep_hours"], 1),
        }
    finally:
        conn.close()


@app.get("/weekly-report")
def weekly_report(user: str):
    today = date.today()
    this_week_start = today - timedelta(days=6)
    last_week_start = today - timedelta(days=13)
    last_week_end = today - timedelta(days=7)

    conn = get_conn()
    try:
        def avg_weight_in_range(start_d, end_d):
            row = conn.execute(
                "SELECT AVG(weight) AS avg_weight FROM records WHERE user = ? AND date BETWEEN ? AND ?",
                (user, start_d.isoformat(), end_d.isoformat()),
            ).fetchone()
            return round(row["avg_weight"], 1) if row["avg_weight"] is not None else None

        this_week_avg = avg_weight_in_range(this_week_start, today)
        last_week_avg = avg_weight_in_range(last_week_start, last_week_end)
    finally:
        conn.close()
    change = (
        round(this_week_avg - last_week_avg, 1)
        if this_week_avg is not None and last_week_avg is not None
        else None
    )

    return {
        "user": user,
        "this_week_avg_weight": this_week_avg,
        "last_week_avg_weight": last_week_avg,
        "change": change,
    }


# ---------- 목표 관리 ----------

@app.post("/goals")
def set_goal(goal: GoalIn):
    data = goal.model_dump()
    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO goals (user, target_weight, target_systolic, target_diastolic)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user) DO UPDATE SET
                target_weight = excluded.target_weight,
                target_systolic = excluded.target_systolic,
                target_diastolic = excluded.target_diastolic
            """,
            (data["user"], data["target_weight"], data["target_systolic"], data["target_diastolic"]),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM goals WHERE user = ?", (goal.user,)).fetchone()
        return dict(row)
    finally:
        conn.close()


@app.get("/goals/{user}")
def get_goal(user: str):
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM goals WHERE user = ?", (user,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="goal not found")
        return dict(row)
    finally:
        conn.close()


@app.get("/goals/{user}/progress")
def get_goal_progress(user: str):
    conn = get_conn()
    try:
        goal_row = conn.execute("SELECT * FROM goals WHERE user = ?", (user,)).fetchone()
        if goal_row is None:
            raise HTTPException(status_code=404, detail="goal not found")
        goal = dict(goal_row)

        first_row = conn.execute(
            "SELECT * FROM records WHERE user = ? ORDER BY date ASC, id ASC LIMIT 1", (user,)
        ).fetchone()
        if first_row is None:
            return {"user": user, "message": "기록이 없어 달성률을 계산할 수 없습니다."}
        latest_row = conn.execute(
            "SELECT * FROM records WHERE user = ? ORDER BY date DESC, id DESC LIMIT 1", (user,)
        ).fetchone()

        first_weight = first_row["weight"]
        latest = dict(latest_row)

        result = {"user": user}

        if goal.get("target_weight") is not None:
            target = goal["target_weight"]
            current = latest["weight"]
            if first_weight == target:
                rate = 100.0
            else:
                rate = (first_weight - current) / (first_weight - target) * 100
                rate = max(0.0, min(100.0, round(rate, 1)))
            result["weight_progress_pct"] = rate
            result["current_weight"] = current
            result["target_weight"] = target

        if goal.get("target_systolic") is not None and goal.get("target_diastolic") is not None:
            achieved = (
                latest["systolic"] <= goal["target_systolic"]
                and latest["diastolic"] <= goal["target_diastolic"]
            )
            result["bp_achieved"] = achieved
            result["current_bp"] = f'{latest["systolic"]}/{latest["diastolic"]}'
            result["target_bp"] = f'{goal["target_systolic"]}/{goal["target_diastolic"]}'

        return result
    finally:
        conn.close()


@app.get("/web", response_class=HTMLResponse)
def web_page():
    with open("static/index.html", encoding="utf-8") as f:
        return f.read()