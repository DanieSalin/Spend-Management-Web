from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django import forms
from django.contrib.auth.models import User
from allauth.account.utils import user_email, user_field, user_username

User = get_user_model()

class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        """
        ✅ Lưu thông tin user khi đăng ký bằng email
        ✅ Tự động xác thực email
        """
        data = form.cleaned_data
        email = data.get('email')
        username = data.get('username')
        name = data.get('name')
        password = data.get('password1')
        user_email(user, email)
        user_username(user, username)
        if name:
            user_field(user, 'name', name)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        self.populate_username(request, user)
        if commit:
            user.save()
            
            # Tự động xác thực email
            EmailAddress.objects.create(
                user=user,
                email=user.email,
                verified=True,
                primary=True
            )
            
        return user

    def clean_email(self, email):
        """
        ✅ Kiểm tra email đã tồn tại chưa
        """
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email này đã được sử dụng.")
        return email

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Invoked just after a user successfully authenticates via a
        social provider, but before the login is actually processed
        (and before the pre_social_login signal is emitted).
        """
        # Ignore existing social accounts, just do this stuff for new ones
        if sociallogin.is_existing:
            return

        # some social logins don't have an email address, e.g. facebook accounts
        # with mobile numbers only, but allauth takes care of that case so just
        # ignore it
        if 'email' not in sociallogin.account.extra_data:
            return

        try:
            # if user exists, connect the account to the existing account and login
            email = sociallogin.account.extra_data['email']
            existing_user = User.objects.get(email=email)
            sociallogin.connect(request, existing_user)
        except User.DoesNotExist:
            # if it does not, let allauth take care of this new social account
            pass

    def populate_user(self, request, sociallogin, data):
        """
        Populates user information from social provider info.
        """
        user = sociallogin.user
        if user.email:
            user.username = user.email.split('@')[0]
        return user 