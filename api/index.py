import os
import requests
import time
import datetime
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

# DB column
# Dorm/floor/washer_num/user_email/end_time
# end time = 세탁기 사용 등록시 현재 시간+소요 시간

def get_washer_info(dormitory, floor):
    # 기숙사와 층으로 필터링
    reservations = db.collection('reservations').where('dormitory', '==', dormitory).where('floor', '==', floor).order_by('washer_number').get() 
    reservation_list = [{'id': res.id, 'data': res.to_dict()} for res in reservations]
    # time(대기 시간)은 소요시간-(현재시간-시작시간)으로 표기
    
    return jsonify(reservation_list), 200

def reserve_idx():
    data = request.json # 클라이언트로부터 JSON 데이터 수신
    dormitory = data.get('dormitory')
    floor = data.get('floor')
    washer_number = data.get('washer_number')
    user_email = data.get('user_email') # e-mail
    end_time = data.get('end_time')
    # start_time = data.get('start_time') # 두개를 합쳐서 end_time으로 가야한다
    # wash_time = data.get('wash_time') # reserve_idx에서는 timer 시간...
    timestamp = firestore.SERVER_TIMESTAMP
    
    # washer_id를 기숙사, 층, 세탁기 번호로 분리하여 저장
    # end_time = start_time + wash_time
    
    # Firestore에 예약 정보 추가
    reservation_ref = db.collection('reservations').add({
        'dormitory': dormitory,
        'floor': floor,
        'washer_number': washer_number,
        'user_email': user_email,
        'end_time' : end_time,
        'timestamp': timestamp
    })
    
    return jsonify({'status': 'success', 'reservation_id': reservation_ref.id}), 201

# 홈페이지 라우트
@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        dormitory = request.form['dormitory']
        floor = int(request.form['floor'])
        washer_info = get_washer_info(dormitory, floor)

        washer_list = []

        # washer_info에서 washer_number만 추출하여 washer_nums 리스트 생성
        washer_nums = [res['data']['washer_number'] for res in washer_info]

        # washer_nums 리스트에서 중복을 제거하여 세탁기 번호 목록 생성
        unique_washer_nums = list(set(washer_nums))

        for washer_num in unique_washer_nums:
            waiting_user = sum(1 for res in washer_info if res['data']['washer_number'] == washer_num)
            # 대기 중인 사용자가 있는 경우에만 대기 시간 계산
            if waiting_user > 0:
                # 대기 중인 모든 사용자의 대기 시간을 리스트로 생성하고, 최솟값을 대기 시간으로 설정
                waiting_times = [res['data']['wait_time'] for res in washer_info if res['data']['washer_number'] == washer_num]
                waiting_time = min(waiting_times)
            else:
                waiting_time = 0
            
            # washer_list에 세탁기 번호, 대기 중인 사용자 수, 대기 시간을 추가
            washer_list.append((washer_num, waiting_user, waiting_time))

        # 최종 데이터를 템플릿으로 전달
        return render_template('index.html', dormitory=dormitory, floor=floor, washer_list=washer_list)
    else:
        # POST 요청인 경우 reserve_idx 함수 실행
        return reserve_idx()


# 세탁기 예약 추가
@app.route('/option', methods=['POST'])

def reserve():
    data = request.json # 클라이언트로부터 JSON 데이터 수신
    dormitory = data.get('dormitory')
    floor = data.get('floor')
    washer_number = data.get('washer_number')
    user_email = data.get('user_email') # e-mail
    end_time = data.get('end_time')
    # start_time = data.get('start_time') # 두개를 합쳐서 end_time으로 가야한다
    # wash_time = data.get('wash_time') # reserve_idx에서는 timer 시간...
    timestamp = firestore.SERVER_TIMESTAMP
    
    # washer_id를 기숙사, 층, 세탁기 번호로 분리하여 저장
    #end_time = start_time + wash_time
    
    # Firestore에 예약 정보 추가
    reservation_ref = db.collection('reservations').add({
        'dormitory': dormitory,
        'floor': floor,
        'washer_number': washer_number,
        'user_email': user_email,
        'end_time' : end_time,
        'timestamp': timestamp
    })
    
    return jsonify({'status': 'success', 'reservation_id': reservation_ref.id}), 201

# 알림 전송시 해당 세탁기에 대한 정보 reset


if __name__ == '__main__':

    app.run(debug=True)

# header(기숙사), under_header(층), (세탁기 번호 => QR로 불러 와야 함)
# QR read시 해당 페이지 뜨도록 하는 것은 => QR 소스코드로 작성
