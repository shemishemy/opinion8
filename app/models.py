# app/models.py

from django.db import models
from django.core.validators import FileExtensionValidator
import os


class FileUpload(models.Model):
    """
    ファイルのアップロード
    """
    title = models.CharField(default='CSVアフィル', max_length=50)
    upload_dir = models.FileField(upload_to='csv', validators=[FileExtensionValidator(['csv',])])
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.title

    def file_name(self):
        """
        相対パスからファイル名のみを取得するカスタムメソッド
        """
        path = os.path.basename(self.upload_dir.name)
        return path