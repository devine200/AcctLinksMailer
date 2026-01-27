from django.db import models
from rest_framework import serializers
from django.contrib.auth.models import User

class EmailTemplateInfo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    website_link = models.URLField()
    website_text = models.CharField(max_length=255)
    telegram_link = models.URLField()
    team = models.CharField(max_length=255, default="Acct Bank Team")
    product_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product_name} by {self.team}"
    
    
class EmailTemplateInfoSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = EmailTemplateInfo
        fields = ['website_link', 'website_text', 'telegram_link', 'team', 'product_name']