from django.contrib import admin
from goods.models import GoodsType, Goods


class BaseModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # 发出任务，让celery worker 重新生成首页静态页
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

    def delete_model(self, request, obj):
        super().delete_model(request, obj)

        # 发出任务，让celery worker 重新生成首页静态页
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()


# Register your models here.
admin.site.register(GoodsType)
admin.site.register(Goods)
