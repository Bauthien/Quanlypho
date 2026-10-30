from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path

from pho_app import views
from pho_app.views import django_admin_disabled

urlpatterns = [
    re_path(r'^admin/.*$', django_admin_disabled),
    path('', include('pho_app.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + [
    re_path(r'^.*$', views.custom_404_view, name='catch_all_404'),
]

handler404 = 'pho_app.views.custom_404_view'
