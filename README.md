이름 : 한승우
소속/반 : 인사교 ai서비스기획
git url : https://github.com/sgelpuy/hyper-healthcare.git
제출일 : 


# 마이 헬스 로그 API

건강 기록(체중·혈압·혈당 등)을 저장하면 BMI 계산, 상태 분류, 경고, 통계를 자동으로 제공하는 API입니다.
user 필드로 사용자별 기록을 분리하고, 목표 관리·주간 리포트·간단한 웹 화면까지 지원합니다.

## 기능 목록

| 메서드 · 경로 | 설명 |
|---|---|
| POST /records | 건강 기록 추가 |
| GET /records | 전체 기록 조회 (user 필터 가능) |
| GET /records/{id} | 기록 단건 조회 |
| PUT /records/{id} | 기록 수정 |
| DELETE /records/{id} | 기록 삭제 |
| GET /search | 날짜 범위 검색 |
| GET /stats | 평균 통계 |
| GET /weekly-report | 주간 리포트 |
| POST /goals | 목표 설정 |
| GET /goals/{user} | 목표 조회 |
| GET /goals/{user}/progress | 목표 달성률 |
| GET /web | 기록 입력/조회 화면 |

## 실행 방법

### 로컬 실행
\`\`\`
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
uvicorn main:app --reload
\`\`\`
접속: http://127.0.0.1:8000/docs

### Docker 실행
\`\`\`
docker build -t my-health-log-api .
docker run -p 8000:8000 my-health-log-api
\`\`\`
접속: http://localhost:8000/docs

## 기술 스택
- FastAPI, Pydantic, uvicorn
- Docker
- HTML/JS (바닐라)

## 배포 URL
(배포했다면 여기에 작성)