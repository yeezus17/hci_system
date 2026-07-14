from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path('hci-mgmt-portal/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('accounts/', include('allauth.socialaccount.urls')),
    path('accounts/google/', include('allauth.socialaccount.providers.google.urls')),  # ← add this

]

urlpatterns += i18n_patterns(
    path('', include('management.urls')),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)