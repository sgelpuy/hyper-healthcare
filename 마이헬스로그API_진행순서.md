# 마이 헬스 로그 API — 진행 순서 (전체 기능 구현 버전)

과제명세서 필수 요구사항 + 5단계 추가 도전 전체(목표관리, 주간리포트, 걸음수 등급, 수면분석, HTML 화면, user 분리)를 포함해 재설계한 순서입니다.
user 필드는 다른 기능들의 기반이 되므로 1단계에서부터 반영합니다.

## 0단계. 준비

- [v] 제출자 정보 작성 (이름, 소속, GitHub URL)
- [v] Python 가상환경 생성 & FastAPI, uvicorn 설치
- [v] GitHub 저장소 생성 (Public)

## 1단계. 데이터 모델 & 기본 CRUD (user 필드 포함)

- [v] 기록 데이터 모델(Pydantic) 정의 — date, weight, height, systolic, diastolic, blood_sugar, steps, sleep_hours, memo, **user**
- [v] `POST /records` 구현 — 기록 추가
- [v] `GET /records`, `GET /records/{id}` 구현 — 목록/단건 조회 (없으면 404)
- [v] `GET /records?user=...` 로 사용자별 필터링 지원
- [v] `DELETE /records/{id}` 구현
- [v] 첫 커밋 & push

> user 구분을 나중에 끼워 넣으면 저장·검색·통계를 전부 다시 손봐야 해서 가장 먼저 넣습니다.

## 2단계. 헬스케어 계산 로직

- [v] BMI 계산 함수 작성 — 몸무게(kg) ÷ 키(m)²
- [v] BMI 분류 (저체중/정상/과체중/비만)
- [v] 혈압 분류 (정상/주의/고혈압)
- [v] 혈당 분류 (정상/공복혈당장애/당뇨 의심)
- [v] warnings 생성 로직 (비만·고혈압·당뇨 의심 시 메시지 추가, 해당 없으면 빈 배열)
- [v] 걸음 수 등급 (부족/적정/우수)
- [v] 수면 분석 (평균 vs 권장 수면 비교)
- [v] 조회 응답에 bmi·bmi_category·bp_category·sugar_category·warnings·걸음수 등급·수면 분석 포함
- [v] `PUT /records/{id}` 구현
- [v] 커밋 & push

> 걸음 수 등급·수면 분석도 "기록 하나 → 값 계산" 패턴이라 BMI/혈압/혈당 분류와 같은 단계에서 처리합니다.

## 3단계. 검색 · 통계 · 주간 리포트 · 파일 저장

- [v] `GET /search` 구현 — 날짜 범위(start, end) 검색, user별 필터링
- [v] `GET /stats` 구현 — 평균 체중 등 통계, user별 필터링
- [v] 주간 리포트 — 최근 7일 평균, 지난주 대비 변화 (user별)
- [v] 기록을 JSON 파일로 저장 (user 정보 포함) → 서버 재시작해도 유지되도록 처리
- [ ] `.gitignore`에 `data.json` 추가
- [ ] 커밋 & push

> 주간 리포트는 결국 "기간별 통계"라 stats 만들 때 같이 설계하면 중복 작업이 줄어듭니다.

## 4단계. 목표 관리 (신규 리소스)

- [ ] 목표 데이터 모델 정의 (user, 목표 체중, 목표 혈압 등)
- [ ] 목표 저장/조회 엔드포인트 구현
- [ ] 달성률 계산 (목표 vs 최근 기록 비교)
- [ ] 커밋 & push

> 지금까지는 "기록(record)"만 다뤘지만 목표관리는 완전히 새로운 리소스라 별도 단계로 둡니다. user별 기록이 쌓여 있어야 달성률 계산이 가능해 1~3단계 이후에 옵니다.

## 5단계. 간단 HTML 화면

- [ ] 기록 입력/조회용 HTML 한 페이지 작성
- [ ] 지금까지 만든 API(records, search, stats 등) 호출해서 화면에 연결
- [ ] 커밋 & push

> 화면은 API의 소비자이므로 API가 다 완성된 뒤 만들어야 헛수고가 없습니다.

## 6단계. Docker & 제출 준비

- [ ] `requirements.txt` 작성
- [ ] `Dockerfile`, `.dockerignore` 작성
- [ ] `docker build` / `docker run` 성공 확인
- [ ] `README.md` 작성 (프로젝트 소개, 엔드포인트 표, 실행 방법, 기술 스택, user 분리·목표관리 등 확장 기능 설명)
- [ ] (가점, 선택) 클라우드 배포 후 공인 IP 접속 확인
- [ ] 최종 커밋 & push

> 기능이 다 확정된 뒤 컨테이너화해야 다시 빌드할 일이 줄어듭니다.

## 7단계. 제출 전 최종 체크

- [ ] 서버 오류 없이 실행, `/docs` 정상 접속
- [ ] 7개 필수 엔드포인트(POST/GET/GET id/PUT/DELETE/search/stats) 모두 동작
- [ ] BMI·분류·경고·통계·걸음수 등급·수면분석 결과 정확
- [ ] user별로 기록이 올바르게 분리되어 조회됨
- [ ] 목표 관리 달성률 계산 정확
- [ ] HTML 화면에서 입력/조회 정상 동작
- [ ] 재시작 후에도 데이터 유지
- [ ] `docker build`/`run` 성공
- [ ] `venv`, `data.json`이 저장소에 올라가지 않음
- [ ] README 작성 완료
- [ ] 최종 코드 push, 저장소 Public 상태
