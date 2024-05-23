from celery import Celery

# Celery 어플리케이션 생성
app = Celery('tasks', broker='redis://localhost:6379/0')

# Celery worker 실행
if __name__ == '__main__':
    app.start()