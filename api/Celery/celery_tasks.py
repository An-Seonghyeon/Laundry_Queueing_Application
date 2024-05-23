from celery import Celery
from celery.schedules import crontab
from datetime import timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import time
import firebase_admin
from firebase_admin import credentials, firestore

# Celery 어플리케이션 생성
app = Celery('tasks', broker='redis://localhost:6379/0')

# Firebase Firestore 연결
cred_path = 'credentials/hd-laundry-qr-firebase-adminsdk-jk05n-e56796e24b.json'
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
db = firestore.client()

# smtplib 연결
# 보내는 사람 정보
me = "보내는 사람 이메일아이디@gmail.com"
my_password = "비밀번호"
# SMTP 서버 연결
s = smtplib.SMTP_SSL('smtp.gmail.com')
s.login(me, my_password)

# 업데이트 함수 정의
@app.task
def update_end_time():
    # 현재 시간 가져오기
    current_time = time.time()

    # 1분을 초 단위로 변환
    one_minute = 60

    # 예약 정보 가져오기
    reservations = db.collection('reservations').get()

    # 예약 정보를 순회하면서 처리
    for res in reservations:
        data = res.to_dict()
        end_time = data.get('end_time')
        user_email = data.get('user_email')

        # 예약 종료 시간(end_time)이 현재 시간보다 1분 이내인 경우
        if end_time - current_time <= one_minute:
            # 이메일 보내기
            msg = MIMEMultipart()
            msg['Subject'] = "세탁기 사용 종료 1분 전 알림"
            msg['From'] = me
            msg['To'] = user_email
            content = "세탁기 사용 종료가 1분 남았습니다."
            part = MIMEText(content, 'plain')
            msg.attach(part)
            s.sendmail(me, user_email, msg.as_string())
            
            # 예약 삭제
            db.collection('reservations').document(res.id).delete()

# 스케줄러 설정
app.conf.beat_schedule = {
    'update-end-time': {
        'task': 'tasks.update_end_time',
        'schedule': timedelta(minutes=1),  # 매 분마다 실행
    },
}
