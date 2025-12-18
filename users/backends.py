from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class PhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        
        try:
            # Check against username OR phone OR email
            # Use filter().first() to avoid MultipleObjectsReturned crash if duplicates exist (e.g. duplicate emails)
            user = User.objects.filter(Q(username=username) | Q(phone=username) | Q(email=username)).first()
            if not user:
                return None
        except User.DoesNotExist:
            return None
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None
