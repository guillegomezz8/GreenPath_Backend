from django.contrib import admin
from django.urls import path,include,re_path
from django.conf import settings
from django.views.static import serve
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from apps.user.views import Login,Logout


urlpatterns = [
    path('admin/', admin.site.urls),

    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    path('logout/', Logout.as_view(), name = 'logout'),
    path('login/',Login.as_view(), name = 'login'),

    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path('users/',include('apps.user.api.routers.user_router')),
    path('workers/',include('apps.user.api.routers.worker_router')),
    path('clients/',include('apps.user.api.routers.client_router')),
    path('companies/',include('apps.company.api.routers')),
    path('routes/',include('apps.route.api.routers')),
    path('collections/',include('apps.collection.api.routers')),
    path('zones/',include('apps.zone.api.routers')),
    path('trucks/',include('apps.truck.api.routers'))
]

urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]

admin.site.site_title = "GreenPath BackOffice"
admin.site.site_header = "GreenPath BackOffice"
admin.site.index_title = "Site administration"