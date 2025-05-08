from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .default_categories import DEFAULT_CATEGORIES

class Category(models.Model):
    """Danh mục chi tiêu hoặc thu nhập"""
    CATEGORY_TYPES = (
        ('income', 'Thu nhập'),
        ('expense', 'Chi tiêu'),
    )
    
    name = models.CharField(max_length=100, verbose_name="Tên danh mục")
    type = models.CharField(max_length=10, choices=CATEGORY_TYPES, verbose_name="Loại danh mục")
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả")
    icon = models.CharField(max_length=50, blank=True, null=True, verbose_name="Icon")
    is_default = models.BooleanField(default=False, verbose_name="Danh mục mặc định")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="categories", verbose_name="Người dùng")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    
    class Meta:
        verbose_name = "Danh mục"
        verbose_name_plural = "Danh mục"
        ordering = ['type', 'name']
        unique_together = ['name', 'user']
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
    
    @classmethod
    def create_default_categories(cls, user):
        """Tạo các danh mục mặc định cho người dùng mới"""
        for category_data in DEFAULT_CATEGORIES:
            # Kiểm tra xem danh mục đã tồn tại chưa
            if not cls.objects.filter(user=user, name=category_data['name']).exists():
                cls.objects.create(
                    user=user,
                    **category_data
                )

class Card(models.Model):
    """Thẻ ngân hàng hoặc ví điện tử"""
    CARD_TYPES = (
        ('credit', 'Thẻ tín dụng'),
        ('debit', 'Thẻ ghi nợ'),
        ('ewallet', 'Ví điện tử'),
        ('cash', 'Tiền mặt'),
        ('other', 'Khác'),
    )
    
    name = models.CharField(max_length=100, verbose_name="Tên thẻ/ví")
    card_type = models.CharField(max_length=10, choices=CARD_TYPES, verbose_name="Loại thẻ/ví")
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Số dư")
    card_number = models.CharField(max_length=30, blank=True, null=True, verbose_name="Số thẻ")
    expiry_date = models.DateField(blank=True, null=True, verbose_name="Ngày hết hạn")
    color = models.CharField(max_length=20, default="#007bff", verbose_name="Màu sắc")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cards", verbose_name="Người dùng")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    
    class Meta:
        verbose_name = "Thẻ/Ví"
        verbose_name_plural = "Thẻ/Ví"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.get_card_type_display()}"

class Goal(models.Model):
    """Mục tiêu tài chính"""
    STATUS_CHOICES = (
        ('in_progress', 'Đang thực hiện'),
        ('completed', 'Hoàn thành'),
        ('cancelled', 'Đã hủy'),
    )
    
    name = models.CharField(max_length=200, verbose_name="Tên mục tiêu")
    target_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Số tiền mục tiêu")
    current_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Số tiền hiện tại")
    start_date = models.DateField(default=timezone.now, verbose_name="Ngày bắt đầu")
    end_date = models.DateField(verbose_name="Ngày kết thúc")
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='in_progress', verbose_name="Trạng thái")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="goals", verbose_name="Người dùng")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    
    class Meta:
        verbose_name = "Mục tiêu"
        verbose_name_plural = "Mục tiêu"
        ordering = ['-end_date']
    
    def __str__(self):
        return self.name
    
    @property
    def progress_percentage(self):
        if self.target_amount == 0:
            return 0
        return min(100, int((self.current_amount / self.target_amount) * 100))

class Budget(models.Model):
    """Ngân sách theo danh mục"""
    PERIOD_CHOICES = (
        ('daily', 'Hàng ngày'),
        ('weekly', 'Hàng tuần'),
        ('monthly', 'Hàng tháng'),
        ('yearly', 'Hàng năm'),
    )
    
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="budgets", verbose_name="Danh mục")
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Số tiền")
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default='monthly', verbose_name="Chu kỳ")
    start_date = models.DateField(default=timezone.now, verbose_name="Ngày bắt đầu")
    end_date = models.DateField(blank=True, null=True, verbose_name="Ngày kết thúc")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="budgets", verbose_name="Người dùng")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    
    class Meta:
        verbose_name = "Ngân sách"
        verbose_name_plural = "Ngân sách"
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.category.name} - {self.get_period_display()} - {self.amount}"
    
    @property
    def is_active(self):
        today = timezone.now().date()
        if self.end_date:
            return self.start_date <= today <= self.end_date
        return self.start_date <= today

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'Thu nhập'),
        ('expense', 'Chi tiêu'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    note = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} VND - {self.date}"

    def save(self, *args, **kwargs):
        # Nếu đây là giao dịch mới
        if not self.pk:
            # Cập nhật số dư thẻ/ví
            if self.transaction_type == 'income':
                self.card.balance += self.amount
            else:  # expense
                self.card.balance -= self.amount
            self.card.save()
        else:
            # Nếu đang cập nhật giao dịch
            old_transaction = Transaction.objects.get(pk=self.pk)
            old_card = old_transaction.card
            
            # Hoàn tác số dư cũ
            if old_transaction.transaction_type == 'income':
                old_card.balance -= old_transaction.amount
            else:  # expense
                old_card.balance += old_transaction.amount
            old_card.save()
            
            # Áp dụng số dư mới
            if self.transaction_type == 'income':
                self.card.balance += self.amount
            else:  # expense
                self.card.balance -= self.amount
            self.card.save()
            
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Hoàn tác số dư thẻ/ví khi xóa giao dịch
        if self.transaction_type == 'income':
            self.card.balance -= self.amount
        else:  # expense
            self.card.balance += self.amount
        self.card.save()
        super().delete(*args, **kwargs)

class GoalContribution(models.Model):
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='contributions')
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    date = models.DateField(auto_now_add=True)
    note = models.TextField(blank=True)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Góp {self.amount} VND vào mục tiêu {self.goal.name}"

    def save(self, *args, **kwargs):
        # Cập nhật số dư thẻ/ví
        self.card.balance -= self.amount
        self.card.save()
        
        # Cập nhật số tiền hiện tại của mục tiêu
        self.goal.current_amount += self.amount
        self.goal.save()
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Hoàn tác số dư thẻ/ví
        self.card.balance += self.amount
        self.card.save()
        
        # Hoàn tác số tiền hiện tại của mục tiêu
        self.goal.current_amount -= self.amount
        self.goal.save()
        
        super().delete(*args, **kwargs)

class GoalTransaction(models.Model):
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='transactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    card = models.ForeignKey(Card, on_delete=models.SET_NULL, null=True)
    note = models.TextField(blank=True)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.goal.name} - {self.amount} - {self.date}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile của {self.user.username}"

    class Meta:
        verbose_name = "Thông tin cá nhân"
        verbose_name_plural = "Thông tin cá nhân"

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('transaction', 'Giao dịch'),
        ('goal', 'Mục tiêu'),
        ('budget', 'Ngân sách'),
        ('system', 'Hệ thống'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Thông báo"
        verbose_name_plural = "Thông báo"
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"