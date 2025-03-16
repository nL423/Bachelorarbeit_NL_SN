from django.urls import path
import newapp.views

subroute = ''

def format_path(prefix, route):
    return f"{prefix}/{route}" if prefix else route

urlpatterns = [
    path(format_path(subroute, ""), newapp.views.index, name='index'),
    path(format_path(subroute, "callback"), newapp.views.callback, name='callback'),
]