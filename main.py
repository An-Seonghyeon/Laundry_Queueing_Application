import requests
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask import Flask, render_template, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore

### Firebase Service Key ###
cred = credentials.Certificate('credentials/hd-laundry-qr-firebase-adminsdk-jk05n-e56796e24b.json')

firebase_admin.initialize_app(cred)

# Firestore 데이터베이스 연결
db = firestore.client()

# Flask 애플리케이션 생성
app = Flask(__name__)

# 홈 페이지 라우트
@app.route('/')
def home():
    return render_template('index.html')


# 세탁기 예약 추가
@app.route('/reserve', methods=['POST'])

def reserve():
    data = request.json # 클라이언트로부터 JSON 데이터 수신
    washer_id = data.get('washer_id')
    user_id = data.get('user_id')
    wash_time = data.get('wash_time')
    
    # Firestore에 예약 정보 추가
    reservation_ref = db.collection('reservations').add({
        'washer_id': washer_id,
        'user_id': user_id,
        'timestamp': firestore.SERVER_TIMESTAMP
        })
    
    return jsonify({'status': 'success', 'reservation_id': reservation_ref[1].id}), 201


# 모든 예약 조회
@app.route('/reservations', methods = ['GET'])

def get_reservations():
    reservations = db.collection('reservations').order_by('timestamp').get()
    reservation_list = [{'id': res.id, 'data': res.to_dict()} for res in reservations]
    
    return jsonify(reservation_list), 200


if __name__ == '__main__':
    app.run(debug=True)