from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [path('admin/', admin.site.urls), path('', views.home, name='home'),
               path('ideas/', views.submit_idea, name='submit_idea'),
               path('idea-images/<int:pk>/', views.idea_image, name='idea_image')]
