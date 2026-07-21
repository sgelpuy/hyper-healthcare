from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date, timedelta

app = FastAPI()

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

records = []
next_id = 1


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
    # 기준: 5,000 미만 부족 / 5,000~9,999 적정 / 10,000 이상 우수
    if steps < 5000:
        return "부족"
    elif steps < 10000:
        return "적정"
    else:
        return "우수"
 
 
def classify_sleep(sleep_hours: float) -> str:
    # 기준: 6시간 미만 부족 / 6~9시간 적정 / 9시간 초과 과다
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
 
 
# ---------- 엔드포인트 ----------
 

@app.get("/")
def read_root():
    return {"message": "hyper-healty API"}
 
 
@app.post("/records")
def create_record(record: RecordIn):
    global next_id
    new_record = record.model_dump()
    new_record["id"] = next_id
    next_id += 1
    records.append(new_record)
    return new_record
 
 
@app.get("/records")
def list_records(user: str | None = None):
    if user is not None:
        filtered = [r for r in records if r["user"] == user]
        return {"count": len(filtered), "records": filtered}
    return {"count": len(records), "records": records}
 
 
@app.get("/records/{record_id}")
def get_record(record_id: int):
    for r in records:
        if r["id"] == record_id:
            return r
    raise HTTPException(status_code=404, detail="record not found")
 
 
@app.put("/records/{record_id}")
def update_record(record_id: int, record: RecordIn):
    for i, r in enumerate(records):
        if r["id"] == record_id:
            updated = record.model_dump()
            updated["id"] = record_id
            records[i] = updated
            return enrich(updated)
    raise HTTPException(status_code=404, detail="record not found")
 
 
@app.delete("/records/{record_id}")
def delete_record(record_id: int):
    for i, r in enumerate(records):
        if r["id"] == record_id:
            deleted = records.pop(i)
            return {"deleted": deleted}
    raise HTTPException(status_code=404, detail="record not found")


@app.get("/search")
def search_records(start: str, end: str, user: str | None = None):
    target = records
    if user is not None:
        target = [r for r in target if r["user"] == user]
    filtered = [r for r in target if start <= r["date"] <= end]
    return {"count": len(filtered), "records": [enrich(r) for r in filtered]}


@app.get("/stats")
def get_stats(user: str | None = None):
    target = records
    if user is not None:
        target = [r for r in target if r["user"] == user]
    if not target:
        return {"count": 0}

    count = len(target)
    return {
        "count": count,
        "avg_weight": round(sum(r["weight"] for r in target) / count, 1),
        "avg_systolic": round(sum(r["systolic"] for r in target) / count, 1),
        "avg_diastolic": round(sum(r["diastolic"] for r in target) / count, 1),
        "avg_blood_sugar": round(sum(r["blood_sugar"] for r in target) / count, 1),
        "avg_steps": round(sum(r["steps"] for r in target) / count, 1),
        "avg_sleep_hours": round(sum(r["sleep_hours"] for r in target) / count, 1),
    }
    
    
@app.get("/weekly-report")
def weekly_report(user: str):
    today = date.today()
    this_week_start = today - timedelta(days=6)
    last_week_start = today - timedelta(days=13)
    last_week_end = today - timedelta(days=7)

    def avg_weight_in_range(start_d, end_d):
        rs = [
            r for r in records
            if r["user"] == user and start_d <= date.fromisoformat(r["date"]) <= end_d
        ]
        return round(sum(r["weight"] for r in rs) / len(rs), 1) if rs else None

    this_week_avg = avg_weight_in_range(this_week_start, today)
    last_week_avg = avg_weight_in_range(last_week_start, last_week_end)
    change = round(this_week_avg - last_week_avg, 1) if this_week_avg is not None and last_week_avg is not None else None

    return {
        "user": user,
        "this_week_avg_weight": this_week_avg,
        "last_week_avg_weight": last_week_avg,
        "change": change,
    }