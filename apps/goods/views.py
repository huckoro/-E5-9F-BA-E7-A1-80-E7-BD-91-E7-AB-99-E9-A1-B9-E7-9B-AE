from django.shortcuts import render
from django.views.generic import View
from goods.models import GoodsType

# Create your views here.

class IndexView(View):
    """首页"""
    def get(self, request):
        """显示"""
        # 获取种类信息
        types = GoodsType.objects.all()

        # 获取用户购物车中商品的数目
        cart_count = 0

        return render(request, 'index.html')
