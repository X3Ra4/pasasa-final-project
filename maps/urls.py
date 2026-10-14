from django.urls import path

from . import views

app_name = "maps"

urlpatterns = [
    path("", views.root_redirect, name="root"),
    path("api/news/", views.news_api, name="news_api"),
    path("api/spots/<slug:spot_slug>/like/", views.spot_like_api, name="spot_like_api"),
    path("api/spots/<slug:spot_slug>/rate/", views.spot_rate_api, name="spot_rate_api"),
    path("api/places/<slug:place_slug>/like/", views.place_like_api, name="place_like_api"),
    path("api/places/<slug:place_slug>/rate/", views.place_rate_api, name="place_rate_api"),
    path("<str:mode>/maps/", views.maps_home, name="maps_home"),
    path("<str:mode>/maps/<slug:map_slug>/", views.map_detail, name="map_detail"),
    path("profile/<str:profile_key>/", views.profile_page, name="profile"),
]
