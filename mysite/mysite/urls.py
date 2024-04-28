from django.urls import path, include
from myapp.views import CinemaHallCreateUpdateAPIView, SessionCreateUpdateListAPIView, TicketCreateListAPIView
from rest_framework import routers

router = routers.SimpleRouter()
router.register(r'cinema-hall', CinemaHallCreateUpdateAPIView, basename='cinema_hall')
router.register(r'session', SessionCreateUpdateListAPIView, basename='session')
router.register(r'ticket', TicketCreateListAPIView, basename='ticket')


urlpatterns = [
    path('auth/', include('myapp.authentication_urls')),
]

urlpatterns += router.urls
