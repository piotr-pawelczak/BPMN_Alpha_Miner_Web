from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.


def home_view(request):
    context = {}
    return render(request, 'bpmn/base.html', context=context)
