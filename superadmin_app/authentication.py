from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone

from superadmin_app.models import UserSession


class SessionJWTAuthentication(
    JWTAuthentication
):

    def authenticate(self, request):

        result = super().authenticate(
            request
        )

        if result is None:
            return None

        user, validated_token = result

        token_jti = validated_token.get('jti')

        if not token_jti:
            raise AuthenticationFailed(
                'Invalid token.'
            )

        current_version = (
            validated_token.get(
                "token_version",
                1
            )
        )

        if (
            current_version
            != user.token_version
        ):
            raise AuthenticationFailed(
                "Session invalidated."
            )

        session = UserSession.objects.filter(
            user=user,
            session_id=token_jti,
            is_active=True
        ).first()

        if not session:

            raise AuthenticationFailed(
                'Session expired or signed out.'
            )

        if session.expires_at and session.expires_at < timezone.now():

            session.is_active = False
            session.save(update_fields=['is_active'])

            raise AuthenticationFailed(
                'Session expired.'
            )

        session.last_activity = timezone.now()
        session.save(update_fields=['last_activity'])

        return (user, validated_token)
    
