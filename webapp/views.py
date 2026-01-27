from django.shortcuts import render

# Create your views here.
def webapp_view(request):
    return render(request, "public/index.html")

def custom_404(request, exception):
    return render(request, '404.html', status=404)