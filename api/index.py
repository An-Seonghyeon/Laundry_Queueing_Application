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
    # Convert floor to the required format
    floor_number = int(floor[1:])
    
    # Reference to the Firestore collections
    washers_ref = db.collection('washers')
    reservations_ref = db.collection('reservations')
    waiting_ref = db.collection('waiting')

    # Fetch dormitory washer configuration
    washer_config_doc = washers_ref.document(dormitory).get()
    if not washer_config_doc.exists:
        return jsonify({'error': 'Dormitory not found'}), 404
    
    washer_config = washer_config_doc.to_dict()
    washers_per_floor = washer_config['washers_per_floor']
    
    washer_info = []

    for washer_num in range(1, washers_per_floor + 1):
        washer_id = f"{dormitory}_{floor_number}_{washer_num}"
        
        # Query reservations for the washer
        reservation_query = reservations_ref.where('washer_id', '==', washer_id).stream()
        reservation_data = next(reservation_query, None)
        end_time = reservation_data.to_dict()['left_time'] if reservation_data else None

        # Query waiting people for the washer
        waiting_query = waiting_ref.where('washer_id', '==', washer_id).stream()
        waiting_people = sum(1 for _ in waiting_query)

        washer_info.append({
            'washer_id': washer_id,
            'number': washer_num,
            'waitingPeople': waiting_people,
            'endTime': end_time
        })

    return washer_info

# def get_washer_info(dormitory, floor):
#     try:
#         floor_number = int(floor[1:])  # Extract the numeric part of the floor (e.g., 'f1' -> 1)
#         reservations = db.collection('reservations').where('dormitory', '==', dormitory).where('floor', '==', floor_number).order_by('washer_number').get()
#         reservation_list = [{'id': res.id, 'data': res.to_dict()} for res in reservations]

#         washers = {}
#         for res in reservation_list:
#             washer_number = res['data']['washer_number']
#             if washer_number not in washers:
#                 washers[washer_number] = {
#                     'number': washer_number,
#                     'waitingPeople': 0,
#                     'endTime': None
#                 }
#             washers[washer_number]['waitingPeople'] += 1
#             if not washers[washer_number]['endTime'] or res['data']['end_time'] < washers[washer_number]['endTime']:
#                 washers[washer_number]['endTime'] = res['data']['end_time']

#         washer_info = list(washers.values())

#         waiting_data = db.collection('waiting').where('washer_id', 'in', [f"{dormitory}_{floor_number}_{washer['number']}" for washer in washer_info]).get()
#         waiting_list = [{'id': wait.id, 'data': wait.to_dict()} for wait in waiting_data]

#         for wait in waiting_list:
#             washer_id = wait['data']['washer_id']
#             left_time = wait['data']['left_time']
#             for washer in washer_info:
#                 if washer['number'] == washer_id.split('_')[-1]:  # assuming washer_id is formatted like dormitory_floor_washer_number
#                     washer['endTime'] = datetime.fromtimestamp(left_time).strftime('%H:%M:%S')

#         return washer_info
#     except Exception as e:
#         print(f"Error in get_washer_info: {e}")
#         traceback.print_exc()
#         return []

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
            'floor': int(floor[1:]),  # Extract numeric part of the floor
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
                washer_list = get_washer_info(dormitory, floor)
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
            washer_list = get_washer_info(dormitory, floor)
            return jsonify(washer_list), 200
            # return jsonify([{'number':1,'endTime':123,'waitingPeople':213}]), 200
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
        end_time = data.get('end_time', None)

        # Calculate the left_time based on mode or end_time
        now = datetime.now()
        if mode == 'standard':
            left_time = now + timedelta(minutes=50)
        elif mode == 'powerful':
            left_time = now + timedelta(minutes=60)
        elif end_time:
            try:
                end_time_minutes = int(end_time)
                left_time = now + timedelta(minutes=end_time_minutes)
            except ValueError as ve:
                return jsonify({'status': 'error', 'message': f'Invalid end_time format: {ve}'}), 400
        else:
            return jsonify({'status': 'error', 'message': 'Invalid mode or end_time selected'}), 400

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
            washer_id = data.get('washer_id')

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
            washer_id = request.args.get('washer_id')  # 여기서 washer_id를 요청에서 받아옵니다.
            return render_template('timer.html', washer_id=washer_id)
    except Exception as e:
        print(f"Error in timer route: {e}")
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)