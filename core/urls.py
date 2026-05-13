from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns # Import this for language-prefixed URLs

# These patterns remain prefix-free (standard)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
     path('accounts/', include('allauth.urls')), # Logic for the language switcher
]

# These patterns will automatically handle /fr/, /ar/, and /en/ prefixes
urlpatterns += i18n_patterns(
    path('', include('management.urls')), # Your H.C.I management logic
    # If you have other apps like 'marketplace', include them here too
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)