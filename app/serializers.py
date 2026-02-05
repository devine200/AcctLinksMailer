from rest_framework import serializers

class EmailTemplateSerializer(serializers.Serializer):
    logo_url = serializers.URLField()
    website_link = serializers.URLField()
    website_text = serializers.CharField(max_length=255)
    telegram_link = serializers.URLField()
    team = serializers.CharField(max_length=255)
    product_name = serializers.CharField(max_length=255)
    livechat_link = serializers.URLField()
    email = serializers.EmailField()
    name = serializers.CharField(max_length=255)