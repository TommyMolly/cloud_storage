from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("api/", lambda request: JsonResponse({"message": "API is working"})),
    path("api/admin/", admin.site.urls),

    path('api/accounts/', include('accounts.urls')),

    path("api/files/", include("files.urls")),

    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
