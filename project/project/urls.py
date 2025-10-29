from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.shop.urls', namespace='shop')),
    path("users/", include("apps.users.urls")),
    path("logout/", include("apps.users.urls")),
    # path('articles/', include('apps.articles.urls')),
]
