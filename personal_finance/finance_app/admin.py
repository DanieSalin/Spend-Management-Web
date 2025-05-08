from django.contrib import admin
from .models import Category, Card, Goal, Budget, Transaction

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

admin.site.register(Category, CategoryAdmin)
admin.site.register(Card, CardAdmin)
admin.site.register(Goal, GoalAdmin)
admin.site.register(Budget, BudgetAdmin)
admin.site.register(Transaction, TransactionAdmin)