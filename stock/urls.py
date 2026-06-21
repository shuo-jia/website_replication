from django.urls import path
from . import views

app_name = "stock"
urlpatterns = [
    path("search", views.searchIndex, name="searchIndex"),
    path("forecast", views.forecast, name="forecast"),
    path("detail/search", views.search, name="search"),
    path("detail/<str:code>/", views.detail, name="detail"),
]
