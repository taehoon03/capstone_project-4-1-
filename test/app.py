from flask import Flask, request, Response, make_response, render_template_string
from flask_cors import CORS
import sqlite3
import json

app = Flask(__name__)
CORS(app)

DB_PATH = 'shop.db'

def json_response(data):
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype='application/json'
    )

def init_db():
    conn = sqlite3.connect(DB_PATH)
    # 기존 테이블 삭제 후 재생성
    conn.execute("DROP TABLE IF EXISTS users")
    conn.execute("DROP TABLE IF EXISTS posts")
    conn.execute("DROP TABLE IF EXISTS accounts")
    conn.execute('''CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        username TEXT, password TEXT,
        phone TEXT, email TEXT
    )''')
    conn.execute('''CREATE TABLE posts (
        id INTEGER PRIMARY KEY,
        content TEXT, author TEXT
    )''')
    conn.execute('''CREATE TABLE accounts (
        id INTEGER PRIMARY KEY,
        username TEXT, balance INTEGER
    )''')
    # 더미 데이터
    conn.execute("INSERT INTO users VALUES (1,'admin','admin1234','010-1234-5678','admin@naver.com')")
    conn.execute("INSERT INTO users VALUES (2,'taehoon','taehoon124','010-5876-5432','taehoon@gmail.com')")
    conn.execute("INSERT INTO users VALUES (3,'chulsoo','kim5678','010-1111-2222','kim@wku.ac.kr')")
    conn.execute("INSERT INTO accounts VALUES (1,'김도영',1000000)")
    conn.execute("INSERT INTO accounts VALUES (2,'김중규',500000)")
    conn.commit()
    conn.close()
       

# SQL Injection 취약한 로그인
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(DB_PATH)
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        try:
            result = conn.execute(query).fetchall()
            if result:
                res = make_response(json_response({
                    "status": "success",
                    "leaked_data": [{"username": r[1], "password": r[2], "phone": r[3], "email": r[4]} for r in result]
                }))
                res.set_cookie('session_id', 'abc123xyz_victim_session')
                res.set_cookie('user', result[0][1])
                res.set_cookie('password', result[0][2])
                res.set_cookie('role', 'admin')
                return res
            return json_response({"status": "fail", "message": "로그인 실패"})
        except Exception as e:
            return json_response({"status": "error", "message": str(e)})

    html = """
    <style>
        body { font-family: Arial; background: #f5f5f5; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-box { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); width: 320px; }
        h2 { text-align: center; color: #333; margin-bottom: 24px; }
        label { font-size: 14px; color: #555; display: block; margin-bottom: 6px; }
        input[type="text"], input[type="password"] { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; margin-bottom: 16px; font-size: 14px; }
        input[type="submit"] { width: 100%; padding: 12px; background: #333; color: white; border: none; border-radius: 6px; font-size: 15px; cursor: pointer; }
        input[type="submit"]:hover { background: #555; }
    </style>
    <div class="login-box">
        <h2>🛒 ShopDemo</h2>
        <form method="post">
            <label>아이디</label>
            <input type="text" name="username" placeholder="아이디 입력"><br>
            <label>비밀번호</label>
            <input type="password" name="password" placeholder="비밀번호 입력"><br>
            <input type="submit" value="로그인">
        </form>
    </div>
    """
    return Response(html, mimetype='text/html')

# XSS 취약한 게시판
@app.route('/board', methods=['GET','POST'])
def board():
    conn = sqlite3.connect(DB_PATH)
    if request.method == 'POST':
        content = request.form['content']
        author = request.form['author']
        conn.execute("INSERT INTO posts (content, author) VALUES (?, ?)", (content, author))
        conn.commit()
    posts = conn.execute("SELECT * FROM posts").fetchall()
    posts_html = ''.join([f"""
        <div style="background:#f9f9f9;border:1px solid #ddd;border-radius:8px;padding:12px;margin:8px 0;">
            <b>✍️ {p[2]}</b>
            <p style="margin:8px 0 0 0;">{p[1]}</p>
        </div>
    """ for p in posts])

    html = """
    <style>
        body { font-family: Arial; max-width: 700px; margin: 40px auto; padding: 0 20px; }
        h2 { color: #333; border-bottom: 2px solid #333; padding-bottom: 10px; }
        .form-box { background: #f0f0f0; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        input[name="author"] { width: 200px; padding: 8px; border: 1px solid #ccc; border-radius: 4px; }
        textarea { width: 100%; height: 100px; padding: 8px; border: 1px solid #ccc; border-radius: 4px; resize: vertical; box-sizing: border-box; }
        input[type="submit"] { background: #333; color: white; padding: 8px 20px; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px; }
        input[type="submit"]:hover { background: #555; }
    </style>
    <h2>📋 게시판</h2>
    <div class="form-box">
        <form method="post">
            이름: <input name="author"><br><br>
            내용:<br>
            <textarea name="content"></textarea><br>
            <input type="submit" value="작성">
        </form>
    </div>
    <hr>
    """ + posts_html

    return Response(html, mimetype='text/html')

# CSRF 취약한 송금
@app.route('/transfer', methods=['GET','POST'])
def transfer():
    conn = sqlite3.connect(DB_PATH)
    if request.method == 'POST':
        amount = request.form['amount']
        to_user = request.form['to']
        conn.execute(f"UPDATE accounts SET balance = balance - {amount} WHERE username = '홍길동'")
        conn.execute(f"UPDATE accounts SET balance = balance + {amount} WHERE username = '{to_user}'")
        conn.commit()
        return jsonify({"status": "success", "message": f"{amount}원이 {to_user}에게 이체됐습니다"})
    accounts = conn.execute("SELECT * FROM accounts").fetchall()
    accounts_html = ''.join([f"<div>{a[1]}: {a[2]}원</div>" for a in accounts])
    return render_template_string(f'''
        <h2>💸 송금</h2>
        {accounts_html}
        <hr>
        <form method="post">
            받는 사람: <input name="to"><br><br>
            금액: <input name="amount"><br><br>
            <input type="submit" value="송금">
        </form>
    ''')
# 탈취된 쿠키 저장소
stolen_cookies = []

# 쿠키 수집 서버 (해커 서버 역할)
@app.route('/steal', methods=['GET'])
def steal():
    cookie = request.args.get('cookie', '없음')
    stolen_cookies.append({
        "time": __import__('datetime').datetime.now().strftime("%H:%M:%S"),
        "cookie": cookie
    })
    return Response("ok", mimetype='text/plain')

# 탈취된 쿠키 확인 페이지
@app.route('/stolen', methods=['GET'])
def stolen():
    html = """
    <h2>💀 탈취된 쿠키 목록</h2>
    <style>
        body { font-family: Arial; background: #1a1a1a; color: #00ff00; padding: 20px; }
        .cookie { background: #333; padding: 10px; margin: 10px 0; border-radius: 5px; }
    </style>
    """
    if stolen_cookies:
        for c in stolen_cookies:
            html += f'<div class="cookie">⏰ {c["time"]}<br>🍪 {c["cookie"]}</div>'
    else:
        html += '<p>아직 탈취된 쿠키 없음</p>'
    return Response(html, mimetype='text/html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)

