from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings

# 自定义文件存储类：https://docs.djangoproject.com/zh-hans/4.0/howto/custom-file-storage/
class FDFSStorage(Storage):
    '''fast dfs文件存储类'''
    def __init__(self, option=None):
        if not option:
            self.option = settings.CUSTOM_STORAGE_OPTIONS
        else:
            self.option = option
    
    def _open(self, name, mode='rb'):
        '''打开文件时使用'''
        pass

    def _save(self, name, content):
        '''保存文件时使用'''
        # name:你选择上传文件的名字
        # content:包含你上传文件内容的File对象
        
        # 创建一个 Fdfs_client 对象
        client = Fdfs_client(conf_path=self.option['CLIENT_CONF'])

        # 上传文件到fast dfs系统中
        # dict {
        #     'Group name'      : group_name,
        #     'Remote file_id'  : remote_file_id,
        #     'Status'          : 'Upload successed.',
        #     'Local file name' : '',
        #     'Uploaded size'   : upload_size,
        #     'Storage IP'      : storage_ip
        # } if success else None

        res = client.upload_by_buffer(content.read())

        if res.get('Status') != 'Upload successed.':
            # 上传失败
            raise Exception('上传文件到fast dfs失败')

        # 获取返回的文件id
        filename = res.get('Remote file_id')

        return filename

    def exists(self, name):
        '''django 判断文件名是否可用'''
        return False

    def url(self, name):
        '''返回访问文件的url路径'''
        return self.option['BASE_URL']+ name

