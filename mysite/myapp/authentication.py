import datetime

from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings


def expires_in(token):
    if not token.user.is_superuser:
        time_left = datetime.datetime.now() - token.created
        Token.objects.filter(key=token).update(created=datetime.datetime.now())
        return time_left
    return datetime.timedelta(seconds=0)


def is_token_expired(token):
    return expires_in(token) > datetime.timedelta(seconds=settings.TOKEN_EXPIRED_AFTER_SECONDS)


def token_expire_handler(token):
    is_expired = is_token_expired(token)
    if is_expired:
        token.delete()
        token = Token.objects.create(user=token.user)
    return token, is_expired


class ExpiringTokenAuthentication(TokenAuthentication):

    def authenticate_credentials(self, key):
        try:
            token = Token.objects.get(key=key)
        except Token.DoesNotExist:
            raise AuthenticationFailed('Invalid Token')

        if not token.user.is_active:
            raise AuthenticationFailed('User is not active')

        token, is_expired = token_expire_handler(token)
        if is_expired:
            raise AuthenticationFailed('The Token is expired')

        return token.user, token
