from flask import Flask, render_template, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import os

### Firebase Service Key ###
cred_path = 'credentials/hd-laundry-qr-firebase-adminsdk-jk05n-e56796e24b.json'
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

# Firestore 데이터베이스 연결
db = firestore.client()

# Flask 애플리케이션 생성
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../templates'))

def get_washer_info(dormitory, floor):
    # 기숙사와 층으로 필터링
    reservations = db.collection('reservations').where('dormitory', '==', dormitory).where('floor', '==', floor).order_by('washer_number').get()
    reservation_list = [{'id': res.id, 'data': res.to_dict()} for res in reservations]
    return reservation_list

def reserve_idx():
    data = request.json # 클라이언트로부터 JSON 데이터 수신
    dormitory = data.get('dormitory')
    floor = data.get('floor')
    washer_number = data.get('washer_number')
    user_email = data.get('user_email')
    end_time = data.get('end_time')
    timestamp = firestore.SERVER_TIMESTAMP

    # Firestore에 예약 정보 추가
    reservation_ref = db.collection('reservations').add({
        'dormitory': dormitory,
        'floor': floor,
        'washer_number': washer_number,
        'user_email': user_email,
        'end_time': end_time,
        'timestamp': timestamp
    })
    
    return jsonify({'status': 'success', 'reservation_id': reservation_ref.id}), 201

# 홈페이지 라우트
@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        dormitory = request.args.get('dormitory')
        floor = int(request.args.get('floor'))
        washer_info = get_washer_info(dormitory, floor)

        washer_list = []
        washer_nums = [res['data']['washer_number'] for res in washer_info]
        unique_washer_nums = list(set(washer_nums))

        for washer_num in unique_washer_nums:
            waiting_user = sum(1 for res in washer_info if res['data']['washer_number'] == washer_num)
            if waiting_user > 0:
                waiting_times = [res['data']['end_time'] for res in washer_info if res['data']['washer_number'] == washer_num]
                waiting_time = min(waiting_times)
            else:
                waiting_time = 0
            
            washer_list.append((washer_num, waiting_user, waiting_time))

        return render_template('index.html', dormitory=dormitory, floor=floor, washer_list=washer_list)
    else:
        return reserve_idx()

# 세탁기 예약 추가 및 washer_id 기반 세탁기 정보 조회
@app.route('/option', methods=['GET', 'POST'])
def option():
    if request.method == 'GET':
        washer_id = request.args.get('washer_id')
        if washer_id:
            # washer_id를 '_'로 분할
            parts = washer_id.split('_')
            dormitory = parts[0]
            floor = parts[1]
            washer_number = parts[2]

            # 첫 번째 다큐먼트만 가져옴
            reservations = db.collection('reservations').where('washer_id', '==', washer_id).limit(1).get()
            reservation_list = [{'id': res.id, 'data': res.to_dict()} for res in reservations]

            if reservation_list:
                reservation = reservation_list[0]
                return render_template('option.html', dormitory=dormitory, floor=floor, washer_number=washer_number, reservation=reservation)
            else:
                return jsonify({'status': 'error', 'message': 'No reservations found for this washer_id'}), 404
        else:
            return jsonify({'status': 'error', 'message': 'washer_id is required'}), 400
    else:
        return reserve_idx()

if __name__ == '__main__':
    app.run(debug=True)
