import random
from typing import Any, Optional, Tuple

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from users.enums import UserTypeChoices
from users.models import User

PROJECT_ENV = settings.PROJECT_ENV
PROJECT_ENV_PROD = settings.PROJECT_ENV_PROD


class AbstractOtpService:
    """
    Abstract base class for OTP (One-Time Password) services.
    Concrete implementations must implement the abstract methods.
    """
    OTP_TIMEOUT_SECONDS: int = 300
    OTP_LENGTH: int = 6

    def __init__(self, obj: Any, purpose: str = 'default', otp_timeout_seconds: Optional[int] = None) -> None:
        self.obj = obj
        self.purpose = purpose
        self.otp_timeout_seconds = otp_timeout_seconds or self.OTP_TIMEOUT_SECONDS

    def get_cache_key(self) -> str:
        model = self.obj.__class__.__name__.lower()
        return f'{self.purpose}:{model}:{self.obj.id}'

    def generate_or_get_otp(self, force: bool = False) -> Tuple[str, bool, int]:
        cache_key = self.get_cache_key()
        otp = cache.get(cache_key)

        if force or not otp:
            otp = self._generate_otp()
            cache.set(cache_key, otp, timeout=self.otp_timeout_seconds)
            self._send_otp_email(str(otp))
            return str(otp), True, self.otp_timeout_seconds

        remaining_time = cache.ttl(cache_key)
        # Redis ttl returns -1 if no expire, -2 if missing. LocMem might return absolute?
        # Standardize:
        if remaining_time is None or remaining_time < 0:
            remaining_time = self.otp_timeout_seconds

        return str(otp), False, remaining_time

    def verify_otp(self, otp: str) -> bool:
        cache_key = self.get_cache_key()
        cached_otp = cache.get(cache_key)
        
        if cached_otp and str(otp) == str(cached_otp):
            cache.delete(cache_key)
            return True
        return False

    def clear_otp(self) -> None:
        cache.delete(self.get_cache_key())

    def _generate_otp(self) -> str:
        # Simplified for development/testing as requested
        if PROJECT_ENV == PROJECT_ENV_PROD:
            return str(random.randint(10 ** (self.OTP_LENGTH - 1), (10 ** self.OTP_LENGTH) - 1))
        return '111111'

    def _send_otp_email(self, otp: str) -> None:
        subject = str(_("Your OTP Code"))
        html_message = render_to_string('users/emails/otp.html', {
            'otp': otp,
            'first_name': getattr(self.obj, 'first_name', ''),
        })
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@saferoute.com')
        send_mail(
            subject,
            '',
            from_email,
            [self.obj.email],
            html_message=html_message,
            fail_silently=False
        )


class DriverOtpService(AbstractOtpService):
    def __init__(self, user: User):
        if not isinstance(user, User) or user.type != UserTypeChoices.DRIVER:
            pass
        super().__init__(user, purpose='driver_otp')


class GuardianOtpService(AbstractOtpService):
    def __init__(self, user: User):
        if not isinstance(user, User) or user.type != UserTypeChoices.GUARDIAN:
            pass
        super().__init__(user, purpose='guardian_otp')
