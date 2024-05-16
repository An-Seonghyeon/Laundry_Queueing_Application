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
    start_time = data.get('start_time')
    wash_time = data.get('wash_time')
    timestamp: firestore.SERVER_TIMESTAMP
    
    # washer_id를 기숙사, 층, 세탁기 번호로 분리하여 저장
    dormitory, floor, washer_number = washer_id.split('_')
    
    # Firestore에 예약 정보 추가
    reservation_ref = db.collection('reservations').add({
        'dormitory': dormitory,
        'floor': floor,
        'washer_number': washer_number,
        'user_id': user_id,
        'start_time' : start_time,
        'wash_time' : wash_time,
        'timestamp': firestore.SERVER_TIMESTAMP
    })
    
    return jsonify({'status': 'success', 'reservation_id': reservation_ref[1].id}), 201


# 예약 조회
def get_reservations(dormitory, floor):
    # 기숙사와 층으로 필터링
    reservations = db.collection('reservations').where('dormitory', '==', dormitory).where('floor', '==', floor).order_by('washer_number').get() 
    reservation_list = [{'id': res.id, 'data': res.to_dict()} for res in reservations]
     # time(대기 시간)은 소요시간-(현재시간-시작시간)으로 표기
    
    return jsonify(reservation_list), 200


if __name__ == '__main__':

    app.run(debug=True)