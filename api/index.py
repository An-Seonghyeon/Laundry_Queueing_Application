from flask import Flask, render_template, request, jsonify, redirect, url_for
import firebase_admin
from firebase_admin import credentials, firestore
import os
import traceback
from datetime import datetime, timedelta

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
    try:
        reservations = db.collection('reservations').where('dormitory', '==', dormitory).where('floor', '==', floor).order_by('washer_number').get()
        reservation_list = [{'id': res.id, 'data': res.to_dict()} for res in reservations]
        return reservation_list
    except Exception as e:
        print(f"Error in get_washer_info: {e}")
        traceback.print_exc()
        return []

def reserve_idx():
    try:
        data = request.json
        dormitory = data.get('dormitory')
        floor = data.get('floor')
        washer_number = data.get('washer_number')
        user_email = data.get('user_email')
        end_time = data.get('end_time')
        timestamp = firestore.SERVER_TIMESTAMP

        reservation_ref = db.collection('reservations').add({
            'dormitory': dormitory,
            'floor': floor,
            'washer_number': washer_number,
            'user_email': user_email,
            'end_time': end_time,
            'timestamp': timestamp
        })

        return jsonify({'status': 'success', 'reservation_id': reservation_ref.id}), 201
    except Exception as e:
        print(f"Error in reserve_idx: {e}")
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/index', methods=['GET', 'POST'])
def index():
    try:
        if request.method == 'GET':
            dormitory = request.args.get('dormitory')
            floor = request.args.get('floor')

            if dormitory and floor:
                floor = int(floor)
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

                    washer_list.append({
                        'number':washer_num, 
                        'waitingPeople': waiting_user, 
                        'endTime': waiting_time})
            else:
                washer_list = []

            return render_template('index.html', dormitory='기숙사를 선택해주세요', floor='층을 선택해주세요', washer_list=washer_list)
        else:
            return reserve_idx()
    except Exception as e:
        print(f"Error in index route: {e}")
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/fetchDataFromFirebase', methods=['GET'])
def fetch_data_from_firebase():
    try:
        dormitory = request.args.get('dormitory')
        floor = request.args.get('floor')

        if dormitory and floor:
            floor = int(floor)
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

                washer_list.append({
                    'number': washer_num,
                    'waitingPeople': waiting_user,
                    'endTime': waiting_time
                })

            return jsonify(washer_list), 200
        else:
            return jsonify([]), 200
        
    except Exception as e:
        print(f"Error in fetch_data_from_firebase: {e}")
        traceback.print_exc()
        
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
@app.route('/option', methods=['GET', 'POST'])
def option():
    try:
        if request.method == 'GET':
            washer_id = request.args.get('washer_id')
            if washer_id:
                parts = washer_id.split('_')
                dormitory = parts[0]
                floor = parts[1]
                washer_number = parts[2]

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
    except Exception as e:
        print(f"Error in option route: {e}")
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/submit_email', methods=['POST'])
def submit_email():
    try:
        data = request.form
        user_email = data.get('email')
        washer_id = data.get('washer_id')
        dormitory = data.get('dormitory')
        floor = data.get('floor')
        washer_number = data.get('washer_number')
        mode = data.get('mode', None)

        # Calculate the left_time based on mode
        now = datetime.now()
        if mode == 'standard':
            left_time = now + timedelta(minutes=50)
        elif mode == 'powerful':
            left_time = now + timedelta(minutes=60)
        else:
            return jsonify({'status': 'error', 'message': 'Invalid mode selected'}), 400

        # Convert left_time to timestamp
        left_time_timestamp = left_time.timestamp()

        db.collection('waiting').add({
            'user_email': user_email,
            'washer_id': washer_id,
            'left_time': left_time_timestamp,
        })

        return render_template('index.html', dormitory=dormitory, floor=floor)
    except Exception as e:
        print(f"Error in submit_email: {e}")
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/timer', methods=['GET', 'POST'])
def timer():
    try:
        if request.method == 'POST':
            data = request.form
            dormitory = data.get('dormitory')
            floor = data.get('floor')
            washer_number = data.get('washer_number')
            end_time = data.get('end_time')

            now = datetime.now()
            end_time_parts = list(map(int, end_time.split(':')))
            left_time = now + timedelta(hours=end_time_parts[0], minutes=end_time_parts[1], seconds=end_time_parts[2])
            left_time_timestamp = left_time.timestamp()

            db.collection('waiting').add({
                'dormitory': dormitory,
                'floor': floor,
                'washer_number': washer_number,
                'left_time': left_time_timestamp,
            })

            return render_template('index.html', dormitory=dormitory, floor=floor)
        else:
            dormitory = request.args.get('dormitory')
            floor = request.args.get('floor')
            washer_number = request.args.get('washer_number')
            return render_template('timer.html', dormitory=dormitory, floor=floor, washer_number=washer_number)
    except Exception as e:
        print(f"Error in timer route: {e}")
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
