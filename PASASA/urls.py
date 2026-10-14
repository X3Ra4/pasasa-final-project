"""
URL configuration for PASASA project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path
from django.views.generic import RedirectView

from maps import views as map_views
from accounts.views import signup
from maps.health import health
from django.contrib.auth.views import LoginView, LogoutView

handler404 = "maps.views.not_found_page"

urlpatterns = [
    path('healthz/', health, name='health'),
    path('catalog/', include('maps.catalog_urls')),
    path('accounts/signup/', signup, name='signup'),
    path('accounts/login/', LoginView.as_view(), name='login'),
    path('accounts/logout/', LogoutView.as_view(), name='logout'),
    path("i18n/", include("django.conf.urls.i18n")),
    path("admin", RedirectView.as_view(url="/admin/", permanent=False)),
    path('admin/', admin.site.urls),
    path("", include("maps.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    re_path(r"^.*$", map_views.not_found_page, name="not_found"),
]
