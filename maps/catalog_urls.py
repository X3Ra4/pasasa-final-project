from django.urls import path
from . import catalog

app_name = 'catalog'
urlpatterns = [
    path('<str:kind>/', catalog.catalog_list, name='list'),
    path('<str:kind>/new/', catalog.catalog_edit, name='create'),
    path('<str:kind>/<int:pk>/', catalog.catalog_detail, name='detail'),
    path('<str:kind>/<int:pk>/edit/', catalog.catalog_edit, name='edit'),
    path('<str:kind>/<int:pk>/delete/', catalog.catalog_delete, name='delete'),
]
