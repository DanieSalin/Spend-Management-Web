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
        try:
            # In ra thông tin debug
            print(f"Pre-social login for: {sociallogin}")
            print(f"Provider: {sociallogin.account.provider}")
            print(f"Has extra data: {bool(sociallogin.account.extra_data)}")
            
            # Nếu đã đăng nhập trước đó, cập nhật thông tin
            if sociallogin.is_existing:
                # Kiểm tra tài khoản có bị khóa không
                if not sociallogin.user.is_active:
                    from django.shortcuts import redirect
                    print(f"User {sociallogin.user.username} is inactive")
                    return redirect('account_inactive')
                    
                # Cập nhật thông tin từ tài khoản Google nếu cần
                if 'email' in sociallogin.account.extra_data:
                    user = sociallogin.user
                    user.email = sociallogin.account.extra_data.get('email', user.email)
                    
                    # Cập nhật first_name và last_name nếu có
                    if 'given_name' in sociallogin.account.extra_data:
                        user.first_name = sociallogin.account.extra_data.get('given_name', user.first_name)
                    if 'family_name' in sociallogin.account.extra_data:
                        user.last_name = sociallogin.account.extra_data.get('family_name', user.last_name)
                    
                    # Lưu thay đổi
                    user.save()
                return

            # Nếu không có email từ tài khoản xã hội, bỏ qua
            if 'email' not in sociallogin.account.extra_data:
                print(f"No email found in social login data")
                return

            # Kiểm tra xem email đã được sử dụng chưa
            email = sociallogin.account.extra_data['email']
            try:
                # Nếu người dùng đã tồn tại, kết nối tài khoản xã hội với tài khoản đó
                existing_user = User.objects.get(email=email)
                
                # Kiểm tra tài khoản có bị khóa không
                if not existing_user.is_active:
                    from django.shortcuts import redirect
                    print(f"User {existing_user.username} is inactive")
                    return redirect('account_inactive')
                    
                sociallogin.connect(request, existing_user)
                print(f"Connected social account to existing user: {existing_user.username}")
            except User.DoesNotExist:
                # Tự động tạo tài khoản mới cho người dùng nếu chưa tồn tại
                print(f"User does not exist for email {email}, will create new user")
                pass
        except Exception as e:
            print(f"Error in pre_social_login: {str(e)}")
            # Không gây lỗi, chỉ ghi log

    def populate_user(self, request, sociallogin, data):
        """
        Populates user information from social provider info.
        """
        try:
            user = sociallogin.user
            
            # Đảm bảo email được cập nhật đúng từ tài khoản Google
            if 'email' in sociallogin.account.extra_data:
                user.email = sociallogin.account.extra_data.get('email')
                
            # Đặt username dựa trên email
            if user.email:
                user.username = user.email.split('@')[0]
                
            # Lấy thông tin họ tên từ tài khoản Google
            if 'given_name' in sociallogin.account.extra_data:
                user.first_name = sociallogin.account.extra_data.get('given_name', '')
            if 'family_name' in sociallogin.account.extra_data:
                user.last_name = sociallogin.account.extra_data.get('family_name', '')
                
            # In log để debug
            print(f"Populate user from Google: email={user.email}, first_name={user.first_name}, last_name={user.last_name}")
            
            return user
        except Exception as e:
            print(f"Error in populate_user: {str(e)}")
            return sociallogin.user
        
    def save_user(self, request, sociallogin, form=None):
        """
        Ghi đè phương thức save_user để đảm bảo email và thông tin cá nhân được lưu đúng cách
        """
        try:
            user = super().save_user(request, sociallogin, form)
            
            # Đảm bảo email được cập nhật một lần nữa sau khi lưu
            if 'email' in sociallogin.account.extra_data:
                user.email = sociallogin.account.extra_data.get('email')
                user.save()
                
            # In log để debug
            print(f"Saved user from Google: id={user.id}, email={user.email}, name={user.get_full_name()}")
            
            return user
        except Exception as e:
            print(f"Error in save_user: {str(e)}")
            if form:
                return super(DefaultSocialAccountAdapter, self).save_user(request, sociallogin.user, form)
            return sociallogin.user
        
    def get_connect_redirect_url(self, request, socialaccount):
        """
        Đặt URL chuyển hướng sau khi đăng nhập bằng mạng xã hội thành công
        """
        return '/home/'
        
    def get_signup_redirect_url(self, request):
        """
        Đặt URL chuyển hướng sau khi đăng ký bằng mạng xã hội thành công
        """
        return '/home/' 