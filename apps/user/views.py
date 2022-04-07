from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from PIL import Image, ImageDraw, ImageFont
from django.utils.six import BytesIO
import re

from django_redis import get_redis_connection
from user.models import User, Address
from goods.models import GoodsSKU

# Create your views here.
class RegisterView(View):
    '''注册'''
    def get(self, request):
        '''显示注册页面'''
        return render(request, 'register.html')

    def post(self, request):
        """处理注册信息"""
        # 获取请求的数据
        user_name = request.POST.get('username')
        password = request.POST.get('password')
        allow = request.POST.get('protocol')

        # 进行数据校验
        if not all([user_name, password]):
            # 数据不完整
            return render(request, 'register.html', {'errmsg':'数据不完整'})

        # 校验用户名
        if not re.match(r'^[A-Za-z0-9][A-Za-z0-9_\-\.]*\@[A-Za-z0-9_\-\.]+\.[A-Za-z]{2,4}$', user_name):
            return render(request, 'register.html', {'errmsg':'邮箱格式错误!'})

        # 校验密码
        if not re.match(r'^.*(?=.{6,})(?=.*\d)(?=.*[a-z])(?=.*[!@#$%^&*? ]).*$', password):
            return render(request, 'register.html', {'errmsg':'密码格式错误!'})

        # 是否同意协议
        if allow != 'on':
            return render(request, 'register.html', {'errmsg':'请同意协议!'})

        # 校验用户名是否重复
        try:
            user = User.objects.get(username=user_name)
        except User.DoesNotExist:
            # 用户名不存在
            user = None
        if user:
            # 用户名存在
            return render(request, 'register.html', {'errmsg':'用户名已存在'})

        # 进行业务处理： 进行用户注册
        user = User.objects.create_user(user_name, email, password)
        user.nick_name = 'nick_name_' + str(user.id)
        user.is_active = 0
        user.save()

        # 发送激活邮件， 包含激活链接：/user/active/
        # 激活链接需要包含用户的身份信息，并且要把身份进行加密
        serializer = Serializer(settings.SECRET_KEY, salt='HOQ9^NXZ^EDa')
        info = [user.id]
        token = serializer.dumps(info)

        # 发送邮件
        send_register_active_email.delay(email, user_name, token)  # 将任务加入任务队列

        # 返回应答， 跳回首页
        return redirect(reverse('article:index'))


# /usr/active/(?P<token>.*)
class ActiveView(View):
    """用户激活"""
    def get(self, request, token):
        """进行用户激活"""
        print(token)
        serializer = Serializer(settings.SECRET_KEY, salt='HOQ9^NXZ^EDa')
        try:
            # 激活链接存在一个小时
            info = serializer.loads(token, max_age=3600)
        except SignatureExpired as e:
            return HttpResponse('激活链接已过期')

        # 获取待激活的用户ID
        user_id = info[0]
        # 根据 id 获取用户信息
        user = User.objects.get(id=user_id)
        user.is_active = 1
        user.save()
        # 跳转到登陆页面
        return redirect(reverse('user:login'))


# /user/login
class LoginView(View):
    """用户登陆"""
    def get(self, request):
        '''登陆页面显示'''
        # 判断是否记住用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''

        # 使用模板
        return render(request, 'login.html', {'username':username, 'checked':checked})

    def post(self, request):
        """登陆校验"""
        # 接收数据
        name = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        verifycode1 = request.POST.get('vcode')  # 获取用户输入的验证码
        verifycode2 = request.session.get('verifycode')  # 获取session中保存的验证码

        # name 判断 是否是用户名或邮箱
        if re.match(r'^[\u4E00-\u9FA5a-zA-Z0-9_]{3,15}$', name):
            # 输入为用户名 判断用户名是否存在
            try:
                user = User.objects.get(username=name)
            except User.DoesNotExist:
                # 用户名不存在
                print(1)
                return render(request, 'login.html', {'errmsg': '用户名或邮箱不存在'})
            # 用户名存在
            user_name = name
        elif re.match(r'^[A-Za-z0-9][A-Za-z0-9_\-\.]*\@[A-Za-z0-9_\-\.]+\.[A-Za-z]{2,4}$', name):
            # 输入为邮箱 判断用户名是否存在
            try:
                user = User.objects.get(email=name)
            except User.DoesNotExist:
                # 用户名不存在
                return render(request, 'login.html', {'errmsg':'用户名或邮箱不存在2'})

            # 用户名存在
            user_name = user.username
        else:
            # 用户名输入错误
            return render(request, 'login.html', {'errmsg':'用户名或邮箱输入错误'})

        # 校验验证码
        if verifycode1 != verifycode2:
            # 验证码错误
            return render(request, 'login.html', {'errmsg':'验证码错误'})

        # 校验数据
        user = authenticate(username=user_name, password=password)
        if user is not None:
            # 用户名密码正确
            if user.is_active:
                # 用户已激活
                # 记录用户登陆状态
                login(request, user)

                # 获取登陆后所要跳转的地址 默认 跳转到首页
                next_url = request.GET.get('next', reverse('article:index'))
                # 跳转到上次访问的页面或首页
                response = redirect(next_url)  # HttpResponseRedirect 对象

                # 判断是否记住用户名
                if remember == 'on':
                    # 记住用户名
                    response.set_cookie('username', user_name, max_age=7*24*3600)
                else:
                    response.delete_cookie('username')

                # 返回response
                return response

            else:
                # 用户未激活
                return render(request, 'login.html', {'errmsg':'账号未激活'})
        else:
            # 用户名或密码错误
            print(1)
            return render(request, 'login.html', {'errmsg':'用户名或密码错误'})


# /user/logout
class LogoutView(View):
    """退出登陆"""
    def get(self, request):
        """退出登陆"""
        # 清楚用户的session信息
        logout(request)

        # 跳转到首页
        return redirect(reverse('article:index'))

# /user/verifycode
class VerifyCode(View):
    """验证码"""
    def get(self, request):
        '''获取验证码'''
        import random

        bgcolor = (random.randrange(20, 100), random.randrange(20, 100), 255)
        width = 100
        height = 25

        im = Image.new('RGB', (width, height), bgcolor)

        draw = ImageDraw.Draw(im)

        for i in range(0, 100):
            xy = (random.randrange(0, width), random.randrange(0, height))
            fill = (random.randrange(0, 255), 255, random.randrange(0, 255))
            draw.point(xy, fill=fill)  # 绘制噪点

        str1 = 'ABCD123EFGHJK456LMNO789PQRSTUVWXYZ'

        rand_str = ''

        for i in range(0, 4):
            rand_str += str1[random.randrange(0, len(str1))]

        # 构造字体对象， ubuntu的字体路径为 '/usr/share/fonts/truetype/freefont'
        font = ImageFont.truetype('NotoMono-Regular.ttf', 23)

        fontcolor = (255, random.randrange(0, 255), random.randrange(0, 255))

        draw.text((5, 2), rand_str[0], font=font, fill=fontcolor)
        draw.text((25, 2), rand_str[1], font=font, fill=fontcolor)
        draw.text((50, 2), rand_str[2], font=font, fill=fontcolor)
        draw.text((75, 2), rand_str[3], font=font, fill=fontcolor)

        del draw

        request.session['verifycode'] = rand_str

        # 内存文件操作
        buf = BytesIO()

        # 将图片保存在内存中，文件类型为 png
        im.save(buf, 'png')

        return HttpResponse(buf.getvalue(), 'image/png')


# /user
class UserInfoView(LoginRequiredMixin, View):
    """用户中心"""
    def get(self, request):
        # 获取user信息
        user = request.user
        address = Address.objects.get_default_address(user)

        # 获取历史浏览记录
        conn = get_redis_connection('default')

        history_key = 'his_%d' % user.id

        # TODO: 获取前五条浏览记录
        sku_ids = conn.lrange(history_ket, 0, 4)  # 返回list

        goods_list = list()

        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            good_list.append(goods)

        # 组织模版上下文
        context = {
            'page': 'info',
            'address': address,
            'goods_list': goods_list
        }

        return render(request, 'center.html', context)


# /user/order
class UserOrderView(LoginRequiredMixin, View):
    """用户订单"""
    def get(self, request):
        # page = "order"
        return render(requset, 'user_order.html', {'page':'order'})


# /user/addr
class AddressView(LoginRequiredMixin, View):
    """地址页"""
    def get(self, request):
        # page = "addr"
        user = request.user

        address = Address.objects.get_default_address(user)

        return render(request, 'user_addr.html', {'page':'addr','address':address})

    def post(self, request):
        """添加地址"""
        # 获取数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        # 校验数据
        if not all([receiver, addr, phone]):
            return render(request, 'user_addr.html', {'errmsg':'数据不完整'})

        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
            return render(request, 'user_addr.html', {'errmsg':'手机格式错误'})

        # 业务处理
        user = request.user
        try:
            address = Address.objects.get(user=user, is_default=True)
        except Address.DoesNotExist:
            address = None

        if address:
            is_default = False
        else:
            is_default = True

        # 添加地址
        Address.objects.create(user=user, addr=addr, receiver=receiver,zip_code=zip_code,phone=phone,is_default=is_default)

        return redirect(reverse('user:address'))
