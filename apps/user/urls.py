"""test_zero URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, re_path
from apps.user.views import RegisterView, ActiveView, LoginView, LogoutView, VerifyCode, UserInfoView, UserOrderView, AddressView

urlpatterns = [
    re_path(r'^register$', RegisterView.as_view(), name='register'),  # 注册
    re_path(r'^active/(?P<token>.*)', ActiveView.as_view(), name='active'),  # 激活
    re_path(r'^verifycode$', VerifyCode.as_view(), name='verify'),  # 验证码
    re_path(r'^logout$', LogoutView.as_view(), name='logout'),  # 退出登陆
    re_path(r'^login$', LoginView.as_view(), name='login'),  # 登陆
    re_path(r'^$', UserInfoView.as_view(), name='info'),  # 用户个人信息
    re_path(r'^order$', UserOrderView.as_view(), name='order'),  # 用户订单
    re_path(r'^address$', AddressView.as_view(), name='address'),  # 地址信息
]
