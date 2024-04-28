import datetime

from django.contrib.auth import authenticate
from django.db.models import Q, F
from rest_framework import serializers
from myapp.models import Customer, CinemaHallModel, SessionModel, TicketModel


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ('username', 'password')


class SignUpSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Customer
        fields = ('username', 'password1', 'password2')
        extra_kwargs = {
            'username': {'required': True},
        }

    def validate(self, attrs):
        if attrs['password1'] != attrs['password2']:
            raise serializers.ValidationError({'password1': 'Password fields didn\'t match.'})

        return attrs

    def create(self, validated_data):
        user = Customer.objects.create(username=validated_data['username'],)
        user.set_password(validated_data['password1'])
        user.save()

        return user


class SignInSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if not authenticate(username=attrs['username'], password=attrs['password']):
            raise serializers.ValidationError('Invalid Credentials or activate account')

        return attrs


class CinemaHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = CinemaHallModel
        fields = '__all__'

    def validate(self, attrs):
        sessions = SessionModel.objects.filter(halls=self.instance,
                                               date__gte=datetime.datetime.now())

        tickets = TicketModel.objects.filter(sessions__in=list(sessions)).exists()

        if tickets:
            raise serializers.ValidationError('Hall has been already activated!')
        return attrs


class SessionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionModel
        fields = [
            'halls',
            'ticket_price',
            'start_date',
            'end_date',
            'date',
        ]

        extra_kwargs = {field: {'required': True} for field in fields}

    def validate(self, attrs):
        hall_form = attrs['halls']
        start_date_form = attrs['start_date']
        end_date_form = attrs['end_date']
        date_form = attrs['date']
        date_range = [start_date_form, end_date_form]

        if start_date_form > end_date_form:
            raise serializers.ValidationError(f'End date can`t be sooner than start date! '
                                              f'({start_date_form}-{end_date_form})')

        session = SessionModel.objects.filter(date=date_form, halls=hall_form)
        session = session.filter(Q(start_date__range=date_range) | Q(end_date__range=date_range))

        if session:
            raise serializers.ValidationError(f'Time coincides with another session! ({session})')

        attrs['available_seats'] = hall_form.size

        return attrs


class SessionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionModel
        fields = '__all__'

    def validate(self, attrs):
        session = self.instance
        tickets = TicketModel.objects.filter(sessions=session).exists()

        if tickets:
            raise serializers.ValidationError({'session': 'Update can`t be applied, as session has been activated!'})

        start_date = attrs['start_date'] if attrs.get('start_date') else session.start_date
        end_date = attrs['end_date'] if attrs.get('end_date') else session.end_date

        if start_date > end_date:
            raise serializers.ValidationError(f'End date can`t be sooner than start date!')

        return attrs


class SessionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionModel
        fields = '__all__'


class SessionInfoSerializer(serializers.Serializer):
    class Meta:
        model = SessionModel
        fields = ['start_date', 'end_date', 'halls']


class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketModel
        fields = ['sessions', 'amount']
        extra_kwargs = {field: {'required': True} for field in fields}

    def validate(self, attrs):
        user = attrs['customers'] = self.context['request'].user
        session = attrs['sessions']
        amount = attrs['amount']

        if not session.available_seats:
            raise serializers.ValidationError({'available_seats': 'No seats are available, Sorry!'})

        elif amount > session.available_seats:
            raise serializers.ValidationError({'amount': f'Amount is bigger than expected!'
                                              f'(Amount: {amount} > Available seats: {session.available_seats})'})

        elif user.purse < session.ticket_price * amount:
            raise serializers.ValidationError({'purse': f'Not enough money on purse! '
                                              f'(Purchase: {session.ticket_price * amount} > Purse: user.purse)'})

        Customer.objects.filter(id=user.id).update(purse=F('purse') - session.ticket_price * amount)
        SessionModel.objects.filter(id=session.id).update(available_seats=F('available_seats') - amount)

        return attrs


class TicketListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketModel
        fields = '__all__'
