import os
from datetime import datetime, timedelta, timezone
from google.oauth2 import service_account
from google.cloud import firestore
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Firebase 인증 정보 설정
firebase_credentials_path = 'firebase_credentials.json'
firebase_credentials = service_account.Credentials.from_service_account_file(firebase_credentials_path)
firebase_db = firestore.Client(credentials=firebase_credentials)

# Gmail 인증 정보 설정
gmail_user = os.getenv('GMAIL_USER', '') # your gmail
gmail_password = os.getenv('GMAIL_PASSWORD', '') # app password 

def send_email(recipient, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, recipient, msg.as_string())
        server.quit()
        print(f"Email sent successfully to {recipient}")
    except Exception as e:
        print(f"Failed to send email to {recipient}: {e}")

def check_end_time_11(request):
    current_time = datetime.now(timezone.utc)
    minute = timedelta(minutes=5)
    
    # 예약 데이터 불러오기
    reservations_ref = firebase_db.collection('waiting')
    all_reservations = reservations_ref.get()

    for res in all_reservations:
        try:
            data = res.to_dict()
            end_time = data.get('left_time')
            user_email = data.get('user_email')
            print(f"Reservation data: {data}") 
            
            
            # 예약 데이터에 있는 notification 컬렉션을 가져옵니다.
            notification_ref = firebase_db.collection('waiting').document(res.id).collection('notify')
            notifications = notification_ref.get()

            # 타임스탬프 문자열을 float으로 변환 후, datetime 객체로 변환
            end_time = datetime.fromtimestamp(float(end_time), tz=timezone.utc)
            print(f"type is : {type({end_time})}")

            # Firestore timestamp 타입을 datetime 객체로 변환
            if isinstance(end_time, datetime):
                
                # Convert current_time to UTC timezone if it's not
                current_time = current_time.astimezone(timezone.utc)
                end_time = end_time.astimezone(timezone.utc)

                print(f"current time(all): {current_time}")
                print(f"End time(all): {end_time}")

                if current_time <= end_time <= current_time + minute:
                    subject = "Laundry machine usage ending soon"
                    body = "Your laundry machine usage will end in 5 minute."

                    # 사용자 이메일 보내기
                    send_email(user_email, subject, body)

                    # 각 notification 문서에서 email 필드 가져오기
                    for notification in notifications:
                        print(f"notification data: {notification}") 
                        email = notification.get('email')
                        if email:
                            send_email(email, subject, body)

                    # Print statements for logging
                    print(f"Email sent successfully to {user_email}")
                    print(f"End time(filter): {end_time}")
            else:
                print(f"Invalid end_time format: {end_time}")

        except Exception as e:
            # 오류 발생 시 기록
            print(f"Failed to process reservation: {e}")


    return 'Function executed successfully.', 200
