"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
from django.http import JsonResponse
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


def api_root(_request):
    return JsonResponse(
        {
            "message": "Zindua assessment API",
            "endpoints": {
                "admin": "/admin/",
                "login": "/api/v1/auth/login/",
                "refresh": "/api/v1/auth/refresh/",
                "assignments": "/api/v1/assignments/",
                "submissions": "/api/v1/submissions/",
            },
        }
    )

urlpatterns = [
    path("", api_root, name="api-root"),
    path("admin/", admin.site.urls),
    path("api-auth/", include("rest_framework.urls")),

    # Auth endpoints — provided by simplejwt out of the box
    path("api/v1/auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/v1/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Classroom endpoints
    path("api/v1/", include("classroom.urls")),
]
