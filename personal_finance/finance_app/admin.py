from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Category, Card, Goal, Budget, Transaction, UserProfile, Notification

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'user', 'created_at')
    list_filter = ('type', 'user')
    search_fields = ('name', 'description')

class CardAdmin(admin.ModelAdmin):
    list_display = ('name', 'card_type', 'balance', 'user', 'created_at')
    list_filter = ('card_type', 'user')
    search_fields = ('name', 'card_number')

class GoalAdmin(admin.ModelAdmin):
    list_display = ('name', 'target_amount', 'current_amount', 'status', 'user', 'end_date')
    list_filter = ('status', 'user')
    search_fields = ('name', 'description')

class BudgetAdmin(admin.ModelAdmin):
    list_display = ('category', 'amount', 'period', 'start_date', 'end_date', 'user')
    list_filter = ('period', 'user', 'category__type')
    search_fields = ('category__name',)

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('amount', 'transaction_type', 'category', 'card', 'date', 'user')
    list_filter = ('transaction_type', 'user', 'date')
    search_fields = ('note', 'category__name', 'card__name')
    date_hierarchy = 'date'

# Đăng ký các model với trang admin
admin.site.register(Category, CategoryAdmin)
admin.site.register(Card, CardAdmin)
admin.site.register(Goal, GoalAdmin)
admin.site.register(Budget, BudgetAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(UserProfile)
admin.site.register(Notification)

# Ghi đè UserAdmin để ngăn chặn việc xóa tài khoản admin
class CustomUserAdmin(UserAdmin):
    def has_delete_permission(self, request, obj=None):
        # Không cho phép xóa tài khoản superuser (admin)
        if obj is not None and obj.is_superuser:
            return False
        return super().has_delete_permission(request, obj)

# Ghi đè đăng ký User model
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)