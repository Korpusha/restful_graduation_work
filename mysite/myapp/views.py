import datetime

from django.contrib.auth import authenticate
from django.db.models import F
from django.db.models import Sum
from myapp.models import Customer, CinemaHallModel, SessionModel, TicketModel
from rest_framework import generics, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND
from rest_framework.views import APIView

from .api import serializers
from .authentication import token_expire_handler


class SignUpView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = serializers.SignUpSerializer
    queryset = Customer.objects.all()


class SignInView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        sign_in_serializer = serializers.SignInSerializer(data=request.data)
        sign_in_serializer.is_valid(raise_exception=True)
        user = authenticate(username=sign_in_serializer.validated_data['username'],
                            password=sign_in_serializer.validated_data['password'])
        serialized_user = serializers.UserSerializer(user)
        token, _ = Token.objects.get_or_create(user=user)
        token, _ = token_expire_handler(token)

        return Response({
            'user': serialized_user.data['username'],
            'token': token.key
        }, status=HTTP_200_OK)


class SignOutView(APIView):
    permission_classes = (IsAuthenticated,)
    queryset = Customer.objects.all()

    def post(self, request):
        request.user.auth_token.delete()
        return Response({
            'user': f'{request.user} was successfully log out'
        }, status=HTTP_200_OK)


class CinemaHallCreateUpdateAPIView(viewsets.ModelViewSet):
    serializer_class = serializers.CinemaHallSerializer
    queryset = CinemaHallModel.objects.all()


class SessionCreateUpdateListAPIView(viewsets.ModelViewSet):
    queryset = SessionModel.objects.all()
    dates = {
        'today': datetime.datetime.today(),
        'tomorrow': datetime.datetime.today() + datetime.timedelta(days=1),
    }

    def get_queryset(self):
        order = self.request.GET.get('order')
        filtration = self.request.GET.get('filtration')
        sessions = SessionModel.objects.filter(date=datetime.datetime.today())

        if filtration:
            sessions = SessionModel.objects.filter(date=self.dates[filtration])
        if order:
            sessions = sessions.order_by(order)

        return sessions

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.SessionCreateSerializer
        elif self.action == 'partial_update' or self.action == 'update':
            return serializers.SessionUpdateSerializer
        elif self.action == 'list' or self.action == 'retrieve':
            return serializers.SessionListSerializer

    @action(detail=False)
    def info(self, request):
        sessions = self.get_queryset()
        halls = request.GET.get('halls')
        start_time = request.GET.get('start_time')
        end_time = request.GET.get('end_time')

        if sessions:
            if halls:
                sessions = sessions.filter(halls=halls)
            if all([start_time, end_time]):
                sessions = sessions.filter(start_date__gte=start_time, start_date__lte=end_time)

            return Response({
                'info': sessions.values()
            }, status=HTTP_200_OK)

        return Response({
            None: 'No sessions found!'
        }, status=HTTP_404_NOT_FOUND)


class TicketCreateListAPIView(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return TicketModel.objects.filter(customers=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.TicketCreateSerializer
        elif self.action == 'list' or self.action == 'retrieve':
            return serializers.TicketListSerializer

    @action(detail=False)
    def total(self, request):
        tickets = self.get_queryset().select_related('sessions')
        tickets = tickets.annotate(total=Sum(F('amount') * F('sessions__ticket_price')))
        total_purchase_sum = tickets.aggregate(total_sum=Sum(F('total')))

        return Response(total_purchase_sum, status=HTTP_200_OK)
