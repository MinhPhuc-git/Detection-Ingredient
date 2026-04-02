from django.contrib import admin
from django.urls import path
from My_App import views

urlpatterns = [
    path('', views.index_view, name="index"),
    path('login/',views.login_view, name="login"),
    path('shop/recipe/',views.predict_model,name="predict_model"),
    path('food',views.food_view,name="food")
]
