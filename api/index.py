import os
import requests
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask import Flask, render_template, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore

### Firebase Service Key ###
cred_path = 'credentials/hd-laundry-qr-firebase-adminsdk-jk05n-e56796e24b.json'
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

# Firestore 데이터베이스 연결
db = firestore.client()

# Flask 애플리케이션 생성
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../templates'))

def get_reservations(dormitory, floor):
    try:
        # 기숙사와 층으로 필터링
        reservations = db.collection('reservations').where('dormitory', '==', dormitory).where('floor', '==', floor).get() 
        reservation_list = [{'id': res.id, 'data': res.to_dict()} for res in reservations]
        # time(대기 시간)은 소요시간-(현재시간-시작시간)으로 표기
        
        return jsonify(reservation_list), 200
    except Exception as e:
        print(f"Error in get_reservations: {e}")
        return jsonify({"error": str(e)}), 500

# 홈페이지 라우트
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def home():
    try:
        if request.method == 'POST':
            dormitory = request.form['dormitory']
            floor = int(request.form['floor'])
        else:
            dormitory = 'kuyper'
            floor = 7
        
        reservation_data, _ = get_reservations(dormitory, floor)
        return render_template('index.html', dormitory=dormitory, floor=floor, reservation_data=reservation_data)
    except Exception as e:
        print(f"Error in home route: {e}")
        return jsonify({"error": str(e)}), 500

# 세탁기 예약 추가
@app.route('/option', methods=['POST'])
def reserve():
    try:
        data = request.json # 클라이언트로부터 JSON 데이터 수신
        washer_id = data.get('washer_id')
        user_id = data.get('user_id')
        start_time = data.get('start_time')
        wash_time = data.get('wash_time')
        
        # washer_id를 기숙사, 층, 세탁기 번호로 분리하여 저장
        dormitory, floor, washer_number = washer_id.split('_')
        
        # Firestore에 예약 정보 추가
        reservation_ref = db.collection('reservations').add({
            'dormitory': dormitory,
            'floor': floor,
            'washer_number': washer_number,
            'user_id': user_id,
            'start_time': start_time,
            'wash_time': wash_time,
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        
        return jsonify({'status': 'success', 'reservation_id': reservation_ref[1].id}), 201
    except Exception as e:
        print(f"Error in reserve route: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ != '__main__':
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)
