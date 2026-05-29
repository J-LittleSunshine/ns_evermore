from django.urls import path, include

urlpatterns = [
    path("iam/", include("ns_backend.iam.urls")),
]
