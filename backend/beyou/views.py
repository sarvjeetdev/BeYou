from django.http import HttpResponse

def home(request):
    return HttpResponse("<h1>Hello, World! BeYou is running successfully.</h1>")
