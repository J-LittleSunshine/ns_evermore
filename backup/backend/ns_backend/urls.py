from django.urls import path, include

urlpatterns = [
    path("iam/", include("iam.urls")),
]
