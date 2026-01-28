from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from django.contrib.auth.models import User

from .mail_handler import send_batch_message, send_single_message
from .models import EmailTemplateInfo, EmailTemplateInfoSerializer

class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        
        if not email or not password:
            return Response({"error": "email and password are required"}, status=400)
        
        try:
            user = User.objects.get(email=email)
            
            if not user.check_password(password):
                return Response({"error": "Invalid credentials"}, status=401)
            
            token, _ = Token.objects.get_or_create(user=user)
            template = EmailTemplateInfo.objects.first() 
            template_serializer = EmailTemplateInfoSerializer(template)
            return Response(status=200, data={"token": token.key, "template": template_serializer.data if template else None})
        
        except User.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=401)
    
        except Exception as e:
            print(str(e))
            return Response(data={"error": "unexpected server error"}, status=500)
        
        
class BatchEmailView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        website_link = request.data.get("websiteLink")
        website_text = request.data.get("websiteText")
        telegram_link = request.data.get("telegramLink")
        team = request.data.get("team")
        product_name = request.data.get("productName")
        livechat_link = request.data.get("liveChatLink")
        
        if not all([website_link, website_text, telegram_link, team, product_name, livechat_link]):
            return Response({"error": "required field missing"}, status=400)
        
        try:
            email_resp = send_batch_message({
                "website_link": website_link.replace("https://", ""),
                "website_text": website_text,
                "telegram_link": telegram_link.replace("https://", ""),
                "team": team,
                "product_name": product_name,
                "livechat_link": livechat_link.replace("https://", "")
            })
            template, _ = EmailTemplateInfo.objects.get_or_create(user=request.user)
            template.website_link = website_link
            template.website_text = website_text
            template.telegram_link = telegram_link
            template.team = team
            template.product_name = product_name
            template.livechat_link = livechat_link
            template.save()
            
            return Response(status=200, data={"message": email_resp})
        
        except Exception as e:
            print(f"Mail: {str(e)}")
            return Response({"error": "unexpected server error"}, status=500)
        

class SingleEmailView(APIView): 
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        website_link = request.data.get("websiteLink")
        website_text = request.data.get("websiteText")
        telegram_link = request.data.get("telegramLink")
        team = request.data.get("team")
        product_name = request.data.get("productName")
        livechat_link = request.data.get("liveChatLink")
        
        if not all([website_link, website_text, telegram_link, team, product_name, livechat_link]):
            return Response({"error": "required field missing"}, status=400)
        
        try:
            send_single_message(request.user.email, {
                "website_link": website_link.replace("https://", ""),
                "website_text": website_text,
                "telegram_link": telegram_link.replace("https://", ""),
                "team": team,
                "product_name": product_name,
                "livechat_link": livechat_link.replace("https://", "")
            })
            template, _ = EmailTemplateInfo.objects.get_or_create(user=request.user)
            template.website_link = website_link
            template.website_text = website_text
            template.telegram_link = telegram_link
            template.team = team
            template.product_name = product_name
            template.livechat_link = livechat_link
            template.save()
            
            return Response(status=200, data={"message": "test email sent successfully"})
        
        except Exception as e:
            print(f"Mail: {str(e)}")
            return Response({"error": "unexpected server error"}, status=500)