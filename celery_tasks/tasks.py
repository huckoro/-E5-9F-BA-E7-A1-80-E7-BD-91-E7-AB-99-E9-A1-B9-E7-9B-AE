# 使用celery
from django.core.mail import send_mail
from django.conf import settings
import  celery import Celery

# 在任务处理者一端加这几句 django环境的初始化
# import os
# import django
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_zero.settings')
# django.setup()

# 创建一个Celery类的实例对象
app = Celery('celery_tasks.tasks', broker='redis://127.0.0.1:6379/8')


# 定义任务函数
@app.task
def send_register_active_email(to_email, username, token):
    '''发送激活邮件'''
    # 组织邮件信息
    subject = '哈克神域用户激活信息'
    message = ''
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_message = '<h1>%s&nbsp;欢迎您成为本网站注册用户</h1>请点击下方链接激活您的账户<br/><a href="http:127.0.0.1:8000/user/active/%s">http:127.0.0.1:8000/user/active/%s</a>' % (usrename, token, token)

    send_mail(subject, message, sender, receiver, html_message=html_message)
    

def generate_static_index_html():
    '''产生首页静态页面'''
    pass

