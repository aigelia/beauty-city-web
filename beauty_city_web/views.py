from django.shortcuts import render


def index(request):
    return render(request, 'index.html')


def notes(request):
    return render(request, 'notes.html')


def popup(request):
    return render(request, 'popup.html')


def service(request):
    return render(request, 'service.html')


def service_finally(request):
    return render(request, 'serviceFinally.html')


def admin_page(request):
    return render(request, 'admin.html')
