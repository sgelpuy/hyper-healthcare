from fastapi import FastAPI
from pydantic import BaseModel

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

@app.get("/")
def read_root():
    return {"message": "마이 헬스 로그 API"}
 
 
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
 
 
@app.delete("/records/{record_id}")
def delete_record(record_id: int):
    for i, r in enumerate(records):
        if r["id"] == record_id:
            deleted = records.pop(i)
            return {"deleted": deleted}
    raise HTTPException(status_code=404, detail="record not found")