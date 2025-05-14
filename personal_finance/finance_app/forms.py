from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Category, Card, Goal, Budget, Transaction, GoalContribution, UserProfile, GoalTransaction

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class LoginForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ['username', 'password']

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'type', 'description', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'icon': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean_name(self):
        name = self.cleaned_data['name']
        user = self.instance.user if self.instance.pk else self.initial.get('user')
        # Kiểm tra trùng tên danh mục cho user (không phân biệt loại)
        qs = Category.objects.filter(user=user, name=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Bạn không được đặt tên danh mục giống nhau.")
        return name

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['name'].widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập tên danh mục'})
        self.fields['description'].widget = forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Nhập mô tả danh mục', 'rows': 3})
        self.fields['type'].widget = forms.Select(
            attrs={'class': 'form-control'},
            choices=[
                ('expense', 'Chi tiêu'),
                ('income', 'Thu nhập')
            ]
        )
        
        # Thêm danh sách biểu tượng Font Awesome
        self.fields['icon'].widget = forms.Select(
            attrs={'class': 'form-control select2-icon', 'data-placeholder': 'Chọn hoặc tìm kiếm biểu tượng'},
            choices=[
                # Biểu tượng cơ bản
                ('fa-home', '🏠 Nhà'),
                ('fa-building', '🏢 Tòa nhà'),
                ('fa-house-user', '🏡 Nhà riêng'),
                ('fa-utensils', '🍽️ Ăn uống'),
                ('fa-hamburger', '🍔 Đồ ăn nhanh'),
                ('fa-pizza-slice', '🍕 Pizza'),
                ('fa-coffee', '☕ Cà phê'),
                ('fa-beer', '🍺 Bia'),
                ('fa-wine-glass-alt', '🍷 Rượu'),
                ('fa-shopping-cart', '🛒 Mua sắm'),
                ('fa-store', '🏪 Cửa hàng'),
                ('fa-shopping-bag', '🛍️ Túi mua sắm'),
                ('fa-car', '🚗 Đi lại'),
                ('fa-bus', '🚌 Xe buýt'),
                ('fa-taxi', '🚕 Taxi'),
                ('fa-bicycle', '🚲 Xe đạp'),
                ('fa-motorcycle', '🏍️ Xe máy'),
                ('fa-plane', '✈️ Máy bay'),
                ('fa-train', '🚂 Tàu hỏa'),
                ('fa-ship', '🚢 Tàu thủy'),
                ('fa-heartbeat', '❤️ Sức khỏe'),
                ('fa-hospital', '🏥 Bệnh viện'),
                ('fa-pills', '💊 Thuốc'),
                ('fa-stethoscope', '🩺 Khám bệnh'),
                ('fa-graduation-cap', '🎓 Giáo dục'),
                ('fa-school', '🏫 Trường học'),
                ('fa-book', '📚 Sách'),
                ('fa-pen', '✏️ Bút'),
                ('fa-laptop', '💻 Máy tính'),
                ('fa-mobile-alt', '📱 Điện thoại'),
                ('fa-tablet-alt', '📱 Máy tính bảng'),
                ('fa-tv', '📺 TV'),
                ('fa-headphones', '🎧 Tai nghe'),
                ('fa-camera', '📷 Máy ảnh'),
                ('fa-gamepad', '🎮 Game'),
                ('fa-film', '🎬 Phim'),
                ('fa-music', '🎵 Nhạc'),
                ('fa-tshirt', '👕 Quần áo'),
                ('fa-socks', '🧦 Tất'),
                ('fa-glasses', '👓 Kính'),
                ('fa-ring', '💍 Trang sức'),
                ('fa-wifi', '📶 Internet'),
                ('fa-water', '💧 Nước'),
                ('fa-bolt', '⚡ Điện'),
                ('fa-fire', '🔥 Gas'),
                ('fa-coins', '💰 Tiền mặt'),
                ('fa-money-bill-wave', '💵 Tiền giấy'),
                ('fa-credit-card', '💳 Thẻ tín dụng'),
                ('fa-piggy-bank', '🐷 Tiết kiệm'),
                ('fa-wallet', '👛 Ví'),
                ('fa-hand-holding-usd', '💵 Thu nhập'),
                ('fa-chart-line', '📈 Đầu tư'),
                ('fa-chart-pie', '📊 Thống kê'),
                ('fa-umbrella', '☔ Bảo hiểm'),
                ('fa-gift', '🎁 Quà tặng'),
                ('fa-heart', '❤️ Yêu thương'),
                ('fa-paw', '🐾 Thú cưng'),
                ('fa-briefcase', '💼 Công việc'),
                ('fa-user-tie', '👔 Công việc văn phòng'),
                ('fa-tools', '🔧 Sửa chữa'),
                ('fa-paint-brush', '🎨 Nghệ thuật'),
                ('fa-dumbbell', '🏋️ Thể thao'),
                ('fa-futbol', '⚽ Bóng đá'),
                ('fa-basketball-ball', '🏀 Bóng rổ'),
                ('fa-swimming-pool', '🏊 Bơi lội'),
                ('fa-hiking', '🥾 Leo núi'),
                ('fa-campground', '⛺ Cắm trại'),
                ('fa-umbrella-beach', '🏖️ Biển'),
                ('fa-skiing', '⛷️ Trượt tuyết'),
                ('fa-snowboarding', '🏂 Trượt ván'),
                ('fa-biking', '🚴 Đạp xe'),
                ('fa-running', '🏃 Chạy bộ'),
                ('fa-yoga', '🧘 Yoga'),
                ('fa-pray', '🙏 Tôn giáo'),
                ('fa-church', '⛪ Nhà thờ'),
                ('fa-mosque', '🕌 Nhà thờ Hồi giáo'),
                ('fa-synagogue', '🕍 Giáo đường'),
                ('fa-birthday-cake', '🎂 Sinh nhật'),
                ('fa-glass-cheers', '🥂 Tiệc'),
                ('fa-mask', '🎭 Giải trí'),
                ('fa-theater-masks', '🎭 Kịch'),
                ('fa-magic', '🎩 Ảo thuật'),
                ('fa-hat-wizard', '🧙 Phù thủy'),
                ('fa-ghost', '👻 Halloween'),
                ('fa-tree', '🌲 Giáng sinh'),
                ('fa-snowman', '⛄ Tuyết'),
                ('fa-sun', '☀️ Thời tiết'),
                ('fa-cloud', '☁️ Mây'),
                ('fa-rain', '🌧️ Mưa'),
                ('fa-snowflake', '❄️ Tuyết'),
                ('fa-wind', '🌬️ Gió'),
                ('fa-volcano', '🌋 Núi lửa'),
                ('fa-seedling', '🌱 Cây cối'),
                ('fa-leaf', '🍃 Lá'),
                ('fa-fish', '🐟 Cá'),
                ('fa-dog', '🐶 Chó'),
                ('fa-cat', '🐱 Mèo'),
                ('fa-horse', '🐴 Ngựa'),
                ('fa-cow', '🐮 Bò'),
                ('fa-kiwi-bird', '🐦 Chim'),
                ('fa-dove', '🕊️ Bồ câu'),
                ('fa-dragon', '🐉 Rồng'),
                ('fa-unicorn', '🦄 Kỳ lân'),
                ('fa-spider', '🕷️ Nhện'),
                ('fa-bug', '🐛 Côn trùng'),
                ('fa-butterfly', '🦋 Bướm'),
                ('fa-frog', '🐸 Ếch'),
                ('fa-turtle', '🐢 Rùa'),
                ('fa-snake', '🐍 Rắn'),
                ('fa-dinosaur', '🦖 Khủng long'),
                ('fa-robot', '🤖 Robot'),
                ('fa-alien', '👽 Người ngoài hành tinh'),
                ('fa-rocket', '🚀 Tên lửa'),
                ('fa-satellite', '🛰️ Vệ tinh'),
                ('fa-meteor', '☄️ Thiên thạch'),
                ('fa-moon', '🌙 Mặt trăng'),
                ('fa-sun', '☀️ Mặt trời'),
                ('fa-star', '⭐ Sao'),
                ('fa-rainbow', '🌈 Cầu vồng'),
                ('fa-cloud-moon', '🌙 Đêm mây'),
                ('fa-cloud-sun', '☀️ Ngày mây'),
                ('fa-cloud-rain', '🌧️ Mưa'),
                ('fa-cloud-showers-heavy', '⛈️ Mưa lớn'),
                ('fa-snowflake', '❄️ Tuyết'),
                ('fa-wind', '🌬️ Gió'),
                ('fa-tornado', '🌪️ Lốc xoáy'),
                ('fa-volcano', '🌋 Núi lửa'),
                ('fa-mountain', '⛰️ Núi'),
                ('fa-tree', '🌲 Cây'),
                ('fa-seedling', '🌱 Cây non'),
                ('fa-leaf', '🍃 Lá'),
                ('fa-grass', '🌿 Cỏ'),
                ('fa-flower', '🌸 Hoa'),
                ('fa-rose', '🌹 Hoa hồng'),
                ('fa-seedling', '🌱 Cây mầm'),
                ('fa-apple-alt', '🍎 Táo'),
                ('fa-lemon', '🍋 Chanh'),
                ('fa-pepper-hot', '🌶️ Ớt'),
                ('fa-carrot', '🥕 Cà rốt'),
                ('fa-egg', '🥚 Trứng'),
                ('fa-cheese', '🧀 Phô mai'),
                ('fa-bacon', '🥓 Thịt xông khói'),
                ('fa-hotdog', '🌭 Xúc xích'),
                ('fa-pizza-slice', '🍕 Pizza'),
                ('fa-hamburger', '🍔 Hamburger'),
                ('fa-ice-cream', '🍦 Kem'),
                ('fa-cookie', '🍪 Bánh quy'),
                ('fa-cake', '🍰 Bánh ngọt'),
                ('fa-candy-cane', '🍬 Kẹo'),
                ('fa-lollipop', '🍭 Kẹo mút'),
                ('fa-mug-hot', '☕ Cà phê nóng'),
                ('fa-glass-martini-alt', '🍸 Cocktail'),
                ('fa-wine-bottle', '🍾 Rượu'),
                ('fa-beer', '🍺 Bia'),
                ('fa-cocktail', '🍹 Cocktail'),
                ('fa-whiskey-glass', '🥃 Whiskey'),
                ('fa-wine-glass-alt', '🍷 Rượu vang'),
                ('fa-martini-glass', '🍸 Martini'),
                ('fa-glass-whiskey', '🥃 Whiskey'),
                ('fa-glass-whiskey-rocks', '🥃 Whiskey đá'),
                ('fa-glass-martini', '🍸 Martini'),
                ('fa-glass-martini-alt', '🍸 Martini'),
                ('fa-glass-citrus', '🍹 Nước trái cây'),
                ('fa-glass-water', '🥛 Nước'),
                ('fa-glass-water-droplet', '💧 Nước'),
                ('fa-mug-saucer', '☕ Cà phê'),
                ('fa-mug-hot', '☕ Cà phê nóng'),
                ('fa-mug-tea', '🍵 Trà'),
                ('fa-mug-marshmallows', '☕ Cà phê marshmallow'),
                ('fa-mug-tea-saucer', '🍵 Trà'),
                ('fa-mug-tea-hot', '🍵 Trà nóng'),
                ('fa-mug-tea-sweet', '🍵 Trà ngọt'),
                ('fa-mug-tea-iced', '🍵 Trà đá'),
                ('fa-mug-tea-milk', '🍵 Trà sữa'),
                ('fa-mug-tea-bubble', '🍵 Trà sữa trân châu'),
                ('fa-mug-tea-boba', '🍵 Trà sữa trân châu'),
                ('fa-mug-tea-pearl', '🍵 Trà sữa trân châu'),
                ('fa-mug-tea-tapioca', '🍵 Trà sữa trân châu'),
                ('fa-mug-tea-bubble-tea', '🍵 Trà sữa trân châu'),
                ('fa-mug-tea-bubble-milk-tea', '🍵 Trà sữa trân châu'),
                ('fa-mug-tea-bubble-milk', '🍵 Trà sữa trân châu'),
                ('fa-mug-tea-bubble-milk-bubble', '🍵 Trà sữa trân châu'),
                ('fa-mug-tea-bubble-milk-bubble-tea', '🍵 Trà sữa trân châu'),
            ]
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
            # Nếu là danh mục mặc định, đánh dấu là mặc định
            default_categories = [
                'Ăn uống', 'Chi tiêu hằng ngày', 'Quần áo', 'Mỹ phẩm',
                'Phí giao lưu', 'Y tế', 'Giáo dục', 'Tiền điện',
                'Đi lại', 'Phí liên lạc', 'Tiền nhà'
            ]
            if instance.name in default_categories:
                instance.is_default = True
        if commit:
            instance.save()
        return instance

class CardForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = ['name', 'card_type', 'balance', 'card_number', 'expiry_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập tên thẻ/ví'}),
            'card_type': forms.Select(attrs={'class': 'form-control'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Nhập số dư'}),
            'card_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập số thẻ (nếu có)'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
        labels = {
            'name': 'Tên thẻ/ví',
            'card_type': 'Loại thẻ/ví',
            'balance': 'Số dư (VNĐ)',
            'card_number': 'Số thẻ (tùy chọn)',
            'expiry_date': 'Ngày hết hạn (tùy chọn)',
        }

    def clean_card_number(self):
        card_number = self.cleaned_data.get('card_number')
        card_type = self.cleaned_data.get('card_type')
        
        if card_number:
            # Loại bỏ khoảng trắng và dấu gạch ngang
            card_number = card_number.replace(' ', '').replace('-', '')
            
            # Kiểm tra xem có phải là số không
            if not card_number.isdigit():
                raise forms.ValidationError('Số thẻ chỉ được chứa các chữ số')
            
            # Kiểm tra độ dài dựa trên loại thẻ
            if card_type == 'credit' and len(card_number) != 16:
                raise forms.ValidationError('Số thẻ tín dụng phải có 16 chữ số')
            elif card_type == 'debit' and len(card_number) != 16:
                raise forms.ValidationError('Số thẻ ghi nợ phải có 16 chữ số')
            elif card_type == 'ewallet' and len(card_number) != 11:
                raise forms.ValidationError('Số ví điện tử phải có 11 chữ số')
        
        return card_number

class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['name', 'target_amount', 'start_date', 'end_date', 'description']

class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['category', 'amount', 'period', 'start_date', 'end_date']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Cập nhật queryset cho các trường
            self.fields['category'].queryset = Category.objects.filter(user=user, type='expense')
            
        # Thêm class và placeholder cho các trường
        self.fields['amount'].widget = forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Nhập số tiền'})
        self.fields['period'].widget = forms.Select(
            attrs={'class': 'form-control'},
            choices=[
                ('daily', 'Hằng ngày'),
                ('weekly', 'Hằng tuần'),
                ('monthly', 'Hằng tháng'),
                ('yearly', 'Hằng năm')
            ]
        )
        self.fields['start_date'].widget = forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
        self.fields['end_date'].widget = forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})

        # Thêm label cho các trường
        self.fields['category'].label = 'Danh mục'
        self.fields['amount'].label = 'Số tiền (VND)'
        self.fields['period'].label = 'Kỳ hạn'
        self.fields['start_date'].label = 'Ngày bắt đầu'
        self.fields['end_date'].label = 'Ngày kết thúc'

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['date', 'transaction_type', 'amount', 'card', 'category', 'note']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True,
            }),
            'transaction_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }, choices=[
                ('income', 'Thu nhập'),
                ('expense', 'Chi tiêu'),
            ]),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'required': True,
                'placeholder': 'Nhập số tiền',
            }),
            'card': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'note': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'Nhập ghi chú (không bắt buộc)',
            }),
        }
        labels = {
            'date': 'Ngày giao dịch',
            'transaction_type': 'Loại giao dịch',
            'amount': 'Số tiền',
            'card': 'Thẻ/Ví',
            'category': 'Danh mục',
            'note': 'Ghi chú',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['card'].queryset = user.cards.all()
            self.fields['category'].queryset = user.categories.all()

class GoalContributionForm(forms.ModelForm):
    class Meta:
        model = GoalTransaction
        fields = ['card', 'amount', 'note']
        widgets = {
            'card': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1000',
                'max': '999999999999',  # Giới hạn 12 chữ số
                'step': 'any',
                'placeholder': 'Nhập số tiền muốn góp'
            }),
            'note': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ghi chú (không bắt buộc)'
            })
        }
        labels = {
            'card': 'Chọn thẻ/ví',
            'amount': 'Số tiền góp',
            'note': 'Ghi chú'
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.goal = kwargs.pop('goal', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['card'].queryset = Card.objects.filter(user=self.user)
            self.fields['card'].empty_label = '-- Chọn thẻ/ví --'

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is None:
            raise forms.ValidationError('Vui lòng nhập số tiền góp')
            
        if amount < 1000:
            raise forms.ValidationError('Số tiền góp tối thiểu là 1,000 VNĐ')
            
        if len(str(int(amount))) > 12:
            raise forms.ValidationError('Số tiền không được vượt quá 12 chữ số')
            
        if self.goal:
            remaining = self.goal.target_amount - self.goal.current_amount
            if amount > remaining:
                raise forms.ValidationError(
                    f'Số tiền góp không được vượt quá số tiền còn thiếu ({remaining:,.0f} VNĐ)'
                )
                
            card = self.cleaned_data.get('card')
            if card and amount > card.balance:
                raise forms.ValidationError('Số dư không đủ để thực hiện giao dịch')
                
        return amount

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar']
        widgets = {
            'avatar': forms.FileInput(attrs={'class': 'form-control'})
        }