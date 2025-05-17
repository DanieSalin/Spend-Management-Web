from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.template.loader import render_to_string
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, TemplateView, DetailView, View
)
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.humanize.templatetags.humanize import intcomma
import json
from decimal import Decimal
from django.contrib.auth import logout
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST
from django.db import transaction
from django.core.exceptions import ValidationError
import xlsxwriter
from io import BytesIO

from .models import Category, Card, Goal, Budget, Transaction, GoalContribution, GoalTransaction, UserProfile, Notification
from .forms import RegisterForm, LoginForm, CategoryForm, CardForm, GoalForm, BudgetForm, TransactionForm, GoalContributionForm, UserProfileForm

class LandingView(TemplateView):
    template_name = 'finance_app/landing.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_users'] = User.objects.count()
        context['total_transactions'] = Transaction.objects.count()
        context['total_goals'] = Goal.objects.count()
        return context

# Trang đăng ký
class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        try:
            # Tạo danh mục mặc định cho người dùng mới
            Category.create_default_categories(self.object)
        except Exception as e:
            messages.error(self.request, f"Có lỗi xảy ra khi tạo danh mục mặc định: {str(e)}")
        return response

# Trang đăng nhập
class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        # Kiểm tra trạng thái tài khoản
        user = form.get_user()
        if not user.is_active:
            messages.error(self.request, 'Tài khoản của bạn đã bị khóa. Vui lòng liên hệ quản trị viên.')
            return self.form_invalid(form)
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('finance_app:index')

# Trang chủ (Dashboard)
@login_required
def dashboard(request):
    today = timezone.now().date()
    start_month = today.replace(day=1)
    
    # Tổng số dư
    total_balance = Card.objects.filter(user=request.user).aggregate(Sum('balance'))['balance__sum'] or 0
    
    # Thu nhập/chi tiêu trong tháng này
    income_this_month = Transaction.objects.filter(
        user=request.user, 
        transaction_type='income',
        date__gte=start_month
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    expense_this_month = Transaction.objects.filter(
        user=request.user, 
        transaction_type='expense',
        date__gte=start_month
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Số giao dịch trong tháng
    transaction_count = Transaction.objects.filter(
        user=request.user,
        date__gte=start_month
    ).count()
    
    # Lấy các mục tiêu đang thực hiện
    goals = Goal.objects.filter(
        user=request.user,
        status='in_progress'
    ).order_by('-end_date')[:5]
    
    context = {
        'total_income': income_this_month,
        'total_expense': expense_this_month,
        'current_balance': total_balance,
        'transaction_count': transaction_count,
        'goals': goals,
    }
    
    return render(request, 'index.html', context)

# Quản lý danh mục
class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'finance_app/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = self.request.user.is_superuser
        return context

class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'finance_app/category_form.html'
    success_url = reverse_lazy('finance_app:category-list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial'] = {'user': self.request.user}
        return kwargs
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        
        # Lấy admin user
        User = get_user_model()
        admin_user = User.objects.filter(is_superuser=True).first()
        
        # Tạo danh sách người dùng cần thông báo
        users_to_notify = [self.request.user]
        if admin_user and admin_user != self.request.user:
            users_to_notify.append(admin_user)
            
        create_notification(
            users=users_to_notify,
            title='Danh mục mới',
            message=f'Bạn đã tạo một danh mục mới: {form.instance.name} - {form.instance.get_type_display()}',
            notification_type='system'
        )
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, "Vui lòng kiểm tra lại thông tin.")
        return super().form_invalid(form)

class CategoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'finance_app/category_form.html'
    success_url = reverse_lazy('finance_app:category-list')
    
    def test_func(self):
        category = self.get_object()
        return category.user == self.request.user

    def form_valid(self, form):
        response = super().form_valid(form)
        create_notification(
            self.request.user,
            'Cập nhật danh mục',
            f'Bạn đã cập nhật danh mục: {form.instance.name}',
            'system'
        )
        return response

class CategoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Category
    template_name = 'finance_app/category_confirm_delete.html'
    success_url = reverse_lazy('finance_app:category-list')
    
    def test_func(self):
        category = self.get_object()
        return category.user == self.request.user
        
    def delete(self, request, *args, **kwargs):
        print(f"--- Bắt đầu thực thi delete() cho Category --- ID: {kwargs.get('pk')}") # DEBUG START
        category = self.get_object()
        print("--- Đã lấy đối tượng Category --- ") # DEBUG GET OBJECT
        
        # Kiểm tra danh mục mặc định trước
        if category.is_default:
            messages.error(request, 'Không thể xóa danh mục mặc định!')
            return redirect('finance_app:category-list')
            
        try:
            # Lấy thông tin cần thiết TRƯỚC khi xóa
            category_name = category.name
            category_type = category.get_type_display()
            user_to_notify = request.user
            
            # Lấy admin user (nếu cần thông báo cho cả admin)
            User = get_user_model()
            admin_user = User.objects.filter(is_superuser=True).first()
            users_to_notify = [user_to_notify]
            if admin_user and admin_user != user_to_notify:
                users_to_notify.append(admin_user)
                
            # Thêm lệnh print để debug
            print(f"Đang tạo thông báo xóa danh mục: {category_name}")
            
            # Tạo thông báo TRƯỚC khi xóa đối tượng
            create_notification(
                users=users_to_notify,
                title='Xóa danh mục',
                message=f'Danh mục \'{category_name}\' ({category_type}) đã được xóa thành công.', # Cập nhật message rõ ràng hơn
                notification_type='system'
            )
            
            # Thêm lệnh print để xác nhận gọi hàm
            print("Đã gọi hàm tạo thông báo xóa danh mục")
            
            # Thực hiện xóa đối tượng
            response = super().delete(request, *args, **kwargs)
            print(f"Đã thực hiện super().delete() cho danh mục {category_name}") # DEBUG
            messages.success(request, f"Đã xóa danh mục '{category_name}' thành công.") # Thông báo thành công
            return response
            
        except Exception as e:
            print(f"Lỗi khi xóa danh mục hoặc tạo thông báo: {str(e)}")
            messages.error(request, f'Có lỗi xảy ra khi xóa danh mục: {str(e)}')
            return redirect('finance_app:category-list')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def toggle_default_category(request, pk):
    """Toggle trạng thái mặc định của danh mục"""
    try:
        category = get_object_or_404(Category, pk=pk)
        category.is_default = not category.is_default
        category.save()
        
        return JsonResponse({
            'success': True,
            'is_default': category.is_default,
            'message': f'Đã {"thêm" if category.is_default else "bỏ"} danh mục "{category.name}" khỏi danh sách mặc định'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Có lỗi xảy ra: {str(e)}'
        }, status=400)

@login_required
def sync_default_categories(request):
    """Đồng bộ danh mục mặc định cho tất cả người dùng"""
    if not request.user.is_superuser:
        messages.error(request, "Bạn không có quyền thực hiện thao tác này.")
        return redirect('finance_app:category-list')
    
    try:
        # Lấy tất cả người dùng không phải admin
        users = User.objects.exclude(id=request.user.id)
        
        # Lấy tất cả danh mục mặc định của admin
        admin_categories = list(Category.objects.filter(user=request.user, is_default=True))
        
        sync_count = 0  # Số danh mục tạo mới
        update_count = 0  # Số danh mục cập nhật
        delete_count = 0  # Số danh mục xóa
        
        for user in users:
            # Log thông tin user đang xử lý
            print(f"Đang đồng bộ danh mục cho user: {user.username}")
            
            # BƯỚC 1: Xóa tất cả các danh mục mặc định của user không có trong danh sách của admin
            admin_category_names = [c.name for c in admin_categories]
            
            # Lấy tất cả danh mục mặc định của user
            user_default_categories = list(Category.objects.filter(user=user, is_default=True))
            
            # Xóa các danh mục mặc định không còn trong danh sách mặc định của admin
            for user_category in user_default_categories:
                if user_category.name not in admin_category_names:
                    # Xóa hoàn toàn danh mục
                    category_name = user_category.name
                    user_category.delete()
                    delete_count += 1
                    print(f"Đã xóa danh mục '{category_name}' của user {user.username}")
            
            # BƯỚC 2: Thêm/Cập nhật các danh mục mặc định từ admin cho user
            for admin_category in admin_categories:
                try:
                    # Kiểm tra xem danh mục đã tồn tại chưa
                    user_category = Category.objects.get(user=user, name=admin_category.name)
                    
                    # Cập nhật thông tin danh mục (đảm bảo giống hệt admin)
                    updated = False
                    
                    # Kiểm tra từng thuộc tính
                    if user_category.type != admin_category.type:
                        user_category.type = admin_category.type
                        updated = True
                        print(f"Cập nhật loại danh mục '{admin_category.name}' cho user {user.username}")
                        
                    if user_category.description != admin_category.description:
                        user_category.description = admin_category.description
                        updated = True
                        print(f"Cập nhật mô tả danh mục '{admin_category.name}' cho user {user.username}")
                        
                    if user_category.icon != admin_category.icon:
                        user_category.icon = admin_category.icon
                        updated = True
                        print(f"Cập nhật icon danh mục '{admin_category.name}' cho user {user.username}")
                        
                    if not user_category.is_default:
                        user_category.is_default = True
                        updated = True
                        print(f"Đánh dấu danh mục '{admin_category.name}' là mặc định cho user {user.username}")
                    
                    if updated:
                        user_category.save()
                        update_count += 1
                        print(f"Đã cập nhật danh mục '{admin_category.name}' cho user {user.username}")
                        
                except Category.DoesNotExist:
                    # Tạo danh mục mới cho user - sao chép chính xác từ admin
                    Category.objects.create(
                        user=user,
                        name=admin_category.name,
                        type=admin_category.type,
                        description=admin_category.description,
                        icon=admin_category.icon,
                        is_default=True
                    )
                    sync_count += 1
                    print(f"Đã tạo danh mục mới '{admin_category.name}' cho user {user.username}")
        
        # Kiểm tra xem có thay đổi nào không
        if sync_count > 0 or update_count > 0 or delete_count > 0:
            messages.success(
                request, 
                f"Đã đồng bộ thành công: {sync_count} danh mục mới, {update_count} danh mục được cập nhật và {delete_count} danh mục được xóa cho {users.count()} người dùng."
            )
        else:
            messages.info(
                request,
                "Tất cả danh mục mặc định đã được đồng bộ. Không có thay đổi nào."
            )
            
    except Exception as e:
        print(f"Lỗi khi đồng bộ danh mục: {str(e)}")
        messages.error(request, f"Có lỗi xảy ra khi đồng bộ danh mục: {str(e)}")
    
    return redirect('finance_app:category-list')

# Quản lý thẻ
class CardListView(LoginRequiredMixin, ListView):
    model = Card
    template_name = 'finance_app/card_list.html'
    context_object_name = 'cards'
    
    def get_queryset(self):
        return Card.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_balance'] = sum(card.balance for card in context['cards'])
        return context

class CardCreateView(LoginRequiredMixin, CreateView):
    model = Card
    form_class = CardForm
    template_name = 'finance_app/card_form.html'
    success_url = reverse_lazy('finance_app:card-list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        create_notification(
            self.request.user,
            'Thẻ/Ví mới',
            f'Bạn đã tạo một thẻ/ví mới: {form.instance.name} - {form.instance.get_card_type_display()}',
            'system'
        )
        return response

class CardUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Card
    form_class = CardForm
    template_name = 'finance_app/card_form.html'
    success_url = reverse_lazy('finance_app:card-list')
    
    def test_func(self):
        card = self.get_object()
        return card.user == self.request.user

    def form_valid(self, form):
        response = super().form_valid(form)
        create_notification(
            self.request.user,
            'Cập nhật thẻ/ví',
            f'Bạn đã cập nhật thẻ/ví: {form.instance.name}',
            'system'
        )
        return response

class CardDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Card
    template_name = 'finance_app/card_confirm_delete.html'
    success_url = reverse_lazy('finance_app:card-list')
    
    def test_func(self):
        card = self.get_object()
        return card.user == self.request.user

    def delete(self, request, *args, **kwargs):
        card = self.get_object()
        try:
            # Lấy thông tin thẻ/ví trước khi xóa
            card_name = card.name
            card_type = card.get_card_type_display()
            
            # Lấy admin user
            User = get_user_model()
            admin_user = User.objects.filter(is_superuser=True).first()
            
            # Tạo danh sách người dùng cần thông báo
            users_to_notify = [request.user]
            if admin_user and admin_user != request.user:
                users_to_notify.append(admin_user)
            
            # Thêm lệnh print để debug
            print(f"Đang tạo thông báo xóa thẻ/ví: {card_name}")
            
            # Tạo thông báo
            create_notification(
                users=users_to_notify,
                title='Xóa thẻ/ví',
                message=f'Thẻ/ví {card_name} ({card_type}) đã được xóa',
                notification_type='system'
            )
            
            # Xóa card sau khi đã tạo thông báo
            response = super().delete(request, *args, **kwargs)
            print("Đã xóa thẻ/ví thành công")
            return response
        except Exception as e:
            print(f"Lỗi khi xóa thẻ/ví: {str(e)}")
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
            return redirect('finance_app:card-list')

# Quản lý mục tiêu
class GoalListView(LoginRequiredMixin, ListView):
    model = Goal
    template_name = 'finance_app/goal_list.html'
    context_object_name = 'goals'
    
    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cards'] = Card.objects.filter(user=self.request.user)
        return context

class GoalCreateView(LoginRequiredMixin, CreateView):
    model = Goal
    form_class = GoalForm
    template_name = 'finance_app/goal_form.html'
    success_url = reverse_lazy('finance_app:goal-list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        create_notification(
            self.request.user,
            'Mục tiêu mới',
            f'Bạn đã tạo một mục tiêu mới: {form.instance.name} - {form.instance.target_amount} VND',
            'goal'
        )
        return response

class GoalUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Goal
    form_class = GoalForm
    template_name = 'finance_app/goal_form.html'
    success_url = reverse_lazy('finance_app:goal-list')
    
    def test_func(self):
        goal = self.get_object()
        return goal.user == self.request.user

    def form_valid(self, form):
        response = super().form_valid(form)
        create_notification(
            self.request.user,
            'Cập nhật mục tiêu',
            f'Bạn đã cập nhật mục tiêu: {form.instance.name}',
            'goal'
        )
        messages.success(self.request, f'Đã cập nhật mục tiêu {form.instance.name} thành công')
        return response

class GoalDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Goal
    template_name = 'finance_app/goal_confirm_delete.html'
    success_url = reverse_lazy('finance_app:goal-list')
    
    def test_func(self):
        goal = self.get_object()
        return goal.user == self.request.user

    def delete(self, request, *args, **kwargs):
        print(f"--- Bắt đầu thực thi delete() cho Goal --- ID: {kwargs.get('pk')}") # DEBUG START
        goal = self.get_object()
        print("--- Đã lấy đối tượng Goal --- ") # DEBUG GET OBJECT
        try:
            # Lấy thông tin mục tiêu trước khi xóa
            goal_name = goal.name
            goal_amount = goal.target_amount
            user_to_notify = request.user
            
            # Lấy admin user (nếu cần)
            User = get_user_model()
            admin_user = User.objects.filter(is_superuser=True).first()
            users_to_notify = [user_to_notify]
            if admin_user and admin_user != user_to_notify:
                users_to_notify.append(admin_user)
            
            # Thêm lệnh print để debug
            print(f"Đang tạo thông báo xóa mục tiêu: {goal_name}")
            
            # Tạo thông báo TRƯỚC khi xóa
            create_notification(
                users=users_to_notify,
                title='Xóa mục tiêu',
                message=f'Mục tiêu \'{goal_name}\' ({goal_amount:,.0f} VNĐ) đã được xóa',
                notification_type='goal'
            )
            print("Đã gọi hàm tạo thông báo xóa mục tiêu") # DEBUG
            
            # Xóa mục tiêu sau khi đã tạo thông báo
            response = super().delete(request, *args, **kwargs)
            print(f"Đã thực hiện super().delete() cho mục tiêu {goal_name}") # DEBUG
            messages.success(request, f"Đã xóa mục tiêu '{goal_name}' thành công.")
            return response
            
        except Exception as e:
            print(f"Lỗi khi xóa mục tiêu hoặc tạo thông báo: {str(e)}")
            messages.error(request, f'Có lỗi xảy ra khi xóa mục tiêu: {str(e)}')
            return redirect('finance_app:goal-list')

class GoalDetailView(LoginRequiredMixin, DetailView):
    model = Goal
    template_name = 'finance_app/goal_detail.html'
    context_object_name = 'goal'

    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        goal = self.object
        
        # Tính số tiền còn thiếu
        context['remaining_amount'] = max(0, goal.target_amount - goal.current_amount)
        
        # Lấy lịch sử giao dịch của mục tiêu này, sắp xếp theo thời gian gần nhất
        transactions = goal.transactions.all().order_by('-date', '-created_at')
        
        # Phân trang cho các giao dịch
        paginator = Paginator(transactions, 10)  # 10 giao dịch mỗi trang
        page = self.request.GET.get('page')
        transactions_page = paginator.get_page(page)
        
        context['transactions'] = transactions_page
        context['total_contributions'] = transactions.count()
        
        # Tính tổng số tiền đã đóng góp
        context['total_contributed'] = transactions.aggregate(total=Sum('amount'))['total'] or 0
        
        # Tính thời gian còn lại
        if goal.status == 'in_progress' and goal.end_date > timezone.now().date():
            days_left = (goal.end_date - timezone.now().date()).days
            context['days_left'] = days_left
        else:
            context['days_left'] = 0
            
        return context

# Quản lý ngân sách
class BudgetListView(LoginRequiredMixin, ListView):
    model = Budget
    template_name = 'finance_app/budget_list.html'
    context_object_name = 'budgets'
    
    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        budgets_with_usage = []
        
        for budget in context['budgets']:
            if budget.period == 'monthly':
                start_date = today.replace(day=1)
            elif budget.period == 'weekly':
                start_date = today - timedelta(days=today.weekday())
            elif budget.period == 'yearly':
                start_date = today.replace(month=1, day=1)
            else:  # daily
                start_date = today
            
            expenses = Transaction.objects.filter(
                user=self.request.user,
                transaction_type='expense',
                category=budget.category,
                date__gte=start_date
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            if budget.amount > 0:
                percentage = min(100, int((expenses / budget.amount) * 100))
            else:
                percentage = 0
                
            budgets_with_usage.append({
                'budget': budget,
                'expenses': expenses,
                'percentage': percentage
            })
        
        context['budgets_with_usage'] = budgets_with_usage
        return context

class BudgetCreateView(LoginRequiredMixin, CreateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'finance_app/budget_form.html'
    success_url = reverse_lazy('finance_app:budget-list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        create_notification(
            self.request.user,
            'Ngân sách mới',
            f'Bạn đã tạo một ngân sách mới: {form.instance.category.name} - {form.instance.amount} VND ({form.instance.get_period_display()})',
            'budget'
        )
        return response

class BudgetUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'finance_app/budget_form.html'
    success_url = reverse_lazy('finance_app:budget-list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def test_func(self):
        budget = self.get_object()
        return budget.user == self.request.user

    def form_valid(self, form):
        response = super().form_valid(form)
        create_notification(
            self.request.user,
            'Cập nhật ngân sách',
            f'Bạn đã cập nhật ngân sách: {form.instance.category.name} - {form.instance.amount} VND',
            'budget'
        )
        return response

class BudgetDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Budget
    template_name = 'finance_app/budget_confirm_delete.html'
    success_url = reverse_lazy('finance_app:budget-list')
    
    def test_func(self):
        budget = self.get_object()
        return budget.user == self.request.user

    def delete(self, request, *args, **kwargs):
        budget = self.get_object()
        try:
            # Lấy thông tin ngân sách trước khi xóa
            budget_category = budget.category.name
            budget_amount = budget.amount
            budget_period = budget.get_period_display()
            
            # Lấy admin user
            User = get_user_model()
            admin_user = User.objects.filter(is_superuser=True).first()
            
            # Tạo danh sách người dùng cần thông báo
            users_to_notify = [request.user]
            if admin_user and admin_user != request.user:
                users_to_notify.append(admin_user)
            
            # Thêm lệnh print để debug
            print(f"Đang tạo thông báo xóa ngân sách: {budget_category}")
            
            # Tạo thông báo
            create_notification(
                users=users_to_notify,
                title='Xóa ngân sách',
                message=f'Ngân sách {budget_category} ({budget_amount:,.0f} VNĐ - {budget_period}) đã được xóa',
                notification_type='budget'
            )
            
            # Xóa ngân sách sau khi đã tạo thông báo
            response = super().delete(request, *args, **kwargs)
            print("Đã xóa ngân sách thành công")
            return response
        except Exception as e:
            print(f"Lỗi khi xóa ngân sách: {str(e)}")
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
            return redirect('finance_app:budget-list')

# Thống kê
@login_required
def statistics_view(request):
    today = timezone.now().date()
    first_day_of_month = today.replace(day=1)
    last_month_start = (first_day_of_month - timedelta(days=1)).replace(day=1)
    
    # Xác định khoảng thời gian
    period = request.GET.get('period', 'month')
    
    if period == 'month':
        start_date = first_day_of_month
        end_date = today
    elif period == 'last_month':
        start_date = last_month_start
        end_date = first_day_of_month - timedelta(days=1)
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
        end_date = today
    elif period == 'custom':
        try:
            start_date = datetime.strptime(request.GET.get('start_date', ''), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.GET.get('end_date', ''), '%Y-%m-%d').date()
        except ValueError:
            start_date = first_day_of_month
            end_date = today
    else:
        start_date = first_day_of_month
        end_date = today
    
    # Tổng thu nhập và chi tiêu
    income_data = Transaction.objects.filter(
        user=request.user,
        transaction_type='income',
        date__gte=start_date,
        date__lte=end_date
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    expense_data = Transaction.objects.filter(
        user=request.user,
        transaction_type='expense',
        date__gte=start_date,
        date__lte=end_date
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    balance = income_data - expense_data
    
    # Chi tiêu theo danh mục
    expense_by_category = Transaction.objects.filter(
        user=request.user,
        transaction_type='expense',
        date__gte=start_date,
        date__lte=end_date
    ).values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    expense_categories = [item['category__name'] for item in expense_by_category]
    expense_amounts = [float(item['total']) for item in expense_by_category]
    
    # Thu nhập theo danh mục
    income_by_category = Transaction.objects.filter(
        user=request.user,
        transaction_type='income',
        date__gte=start_date,
        date__lte=end_date
    ).values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    income_categories = [item['category__name'] for item in income_by_category]
    income_amounts = [float(item['total']) for item in income_by_category]
    
    # Xu hướng theo thời gian
    dates = []
    income_trend = []
    expense_trend = []
    
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.strftime('%d/%m'))
        
        daily_income = Transaction.objects.filter(
            user=request.user,
            transaction_type='income',
            date=current_date
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        income_trend.append(float(daily_income))
        
        daily_expense = Transaction.objects.filter(
            user=request.user,
            transaction_type='expense',
            date=current_date
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        expense_trend.append(float(daily_expense))
        
        current_date += timedelta(days=1)
    
    # Thống kê theo thẻ/ví
    transactions_by_card = Transaction.objects.filter(
        user=request.user,
        date__gte=start_date,
        date__lte=end_date
    ).values('card__name').annotate(
        income=Sum('amount', filter=Q(transaction_type='income')),
        expense=Sum('amount', filter=Q(transaction_type='expense'))
    ).order_by('card__name')
    
    for card in transactions_by_card:
        card['income'] = card['income'] or 0
        card['expense'] = card['expense'] or 0
        card['balance'] = card['income'] - card['expense']
    
    context = {
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'income_data': income_data,
        'expense_data': expense_data,
        'balance': balance,
        'expense_categories': json.dumps(expense_categories),
        'expense_amounts': json.dumps(expense_amounts),
        'income_categories': json.dumps(income_categories),
        'income_amounts': json.dumps(income_amounts),
        'dates': json.dumps(dates),
        'income_trend': json.dumps(income_trend),
        'expense_trend': json.dumps(expense_trend),
        'transactions_by_card': transactions_by_card
    }
    
    return render(request, 'finance_app/statistics.html', context)

# API cho biểu đồ
@login_required
def get_monthly_trend(request):
    today = timezone.now().date()
    first_day_of_current_month = today.replace(day=1)
    months_data = []
    
    # Lấy dữ liệu 6 tháng gần nhất
    for i in range(5, -1, -1):
        target_month = first_day_of_current_month - timedelta(days=1)
        for _ in range(i):
            target_month = target_month.replace(day=1) - timedelta(days=1)
        
        start_date = target_month.replace(day=1)
        if target_month.month == 12:
            end_date = target_month.replace(year=target_month.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = target_month.replace(month=target_month.month + 1, day=1) - timedelta(days=1)
        
        income = Transaction.objects.filter(
            user=request.user,
            transaction_type='income',
            date__gte=start_date,
            date__lte=end_date
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        expense = Transaction.objects.filter(
            user=request.user,
            transaction_type='expense',
            date__gte=start_date,
            date__lte=end_date
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        months_data.append({
            'month': f"{start_date.month}/{start_date.year}",
            'income': income,
            'expense': expense
        })
    
    return JsonResponse(months_data, safe=False)

# Phần Admin
@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    total_transactions = Transaction.objects.count()
    total_categories = Category.objects.count()
    
    recent_users = User.objects.order_by('-date_joined')[:5]
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'total_transactions': total_transactions,
        'total_categories': total_categories,
        'recent_users': recent_users
    }
    
    return render(request, 'admin/admin_dashboard.html', context)

User = get_user_model()

def is_admin(user):
    return user.is_staff

@login_required
@user_passes_test(is_admin)
def admin_user_list(request):
    # Lấy danh sách người dùng
    users = User.objects.all()
    
    # Tạo một list để lưu thông tin chi tiết của mỗi người dùng
    user_details = []
    
    for user in users:
        # Đếm số lượng giao dịch
        transaction_count = Transaction.objects.filter(user=user).count()
        
        # Đếm số lượng ví/thẻ
        card_count = Card.objects.filter(user=user).count()
        
        # Đếm số lượng mục tiêu
        goal_count = Goal.objects.filter(user=user).count()
        
        # Thêm thông tin vào user_details
        user_details.append({
            'user': user,
            'transaction_count': transaction_count,
            'card_count': card_count,
            'goal_count': goal_count
        })
    
    # Sắp xếp theo ngày tham gia mới nhất
    user_details.sort(key=lambda x: x['user'].date_joined, reverse=True)
    
    return render(request, 'finance_app/admin/user_list.html', {
        'user_details': user_details
    })

@login_required
@user_passes_test(is_admin)
def admin_user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.transaction_count = Transaction.objects.filter(user=user).count()
    user.card_count = Card.objects.filter(user=user).count()
    user.goal_count = Goal.objects.filter(user=user).count()
    recent_transactions = Transaction.objects.filter(user=user).order_by('-date')[:5]
    return render(request, 'finance_app/admin/user_detail.html', {
        'user': user,
        'recent_transactions': recent_transactions
    })

@login_required
@user_passes_test(is_admin)
def admin_user_transactions(request, user_id):
    user = get_object_or_404(User, id=user_id)
    transactions = Transaction.objects.filter(user=user).order_by('-date')
    categories = Category.objects.filter(user=user)
    cards = Card.objects.filter(user=user)
    return render(request, 'finance_app/admin/user_transactions.html', {
        'user': user,
        'transactions': transactions,
        'categories': categories,
        'cards': cards
    })

@login_required
@user_passes_test(is_admin)
def admin_toggle_user_status(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        if user.is_superuser:
            return JsonResponse({'success': False, 'message': 'Không thể thay đổi trạng thái của tài khoản admin'})
        if user.id != request.user.id:
            user.is_active = not user.is_active
            user.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'message': 'Không thể thực hiện thao tác với tài khoản của bạn'})
    return JsonResponse({'success': False, 'message': 'Phương thức không được hỗ trợ'})

@login_required
@user_passes_test(is_admin)
def admin_delete_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        if user.is_superuser:
            messages.error(request, 'Không thể xóa tài khoản admin')
            return redirect('finance_app:admin-user-list')
        if user.id != request.user.id:
            user.delete()
            messages.success(request, 'Đã xóa người dùng thành công')
            return redirect('finance_app:admin-user-list')
        messages.error(request, 'Không thể xóa tài khoản của bạn')
    return redirect('finance_app:admin-user-list')


@login_required
@user_passes_test(is_admin)
def admin_transaction_detail(request, transaction_id):
    from .models import Transaction
    transaction = Transaction.objects.select_related('category', 'card', 'user').get(id=transaction_id)
    html = render_to_string('finance_app/admin/transaction_detail_modal.html', {'transaction': transaction})
    return JsonResponse({'success': True, 'html': html})

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'finance_app/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Lấy số lượng giao dịch
        transactions_count = Transaction.objects.filter(user=user).count()

        # Lấy số lượng ví/thẻ
        cards_count = Card.objects.filter(user=user).count()

        # Lấy số lượng mục tiêu
        goals_count = Goal.objects.filter(user=user).count()

        # Tính tổng thu nhập và chi tiêu trong tháng hiện tại
        today = timezone.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_of_month = (start_of_month + relativedelta(months=1)) - timedelta(microseconds=1)

        monthly_transactions = Transaction.objects.filter(
            user=user,
            date__range=(start_of_month, end_of_month)
        )

        monthly_income = monthly_transactions.filter(
            transaction_type='income'
        ).aggregate(total=Sum('amount'))['total'] or 0

        monthly_expense = monthly_transactions.filter(
            transaction_type='expense'
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Lấy giao dịch gần đây
        recent_transactions = Transaction.objects.filter(user=user).order_by('-date')[:5]

        # Thêm dữ liệu vào context
        context.update({
            'transactions_count': transactions_count,
            'cards_count': cards_count,
            'goals_count': goals_count,
            'monthly_income': monthly_income,
            'monthly_expense': monthly_expense,
            'monthly_balance': monthly_income - monthly_expense,
            'recent_transactions': recent_transactions
        })

        return context

class DashboardView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'finance_app/dashboard.html'
    context_object_name = 'transactions'
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).order_by('-date')[:5]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        start_month = today.replace(day=1)
        
        # Thu nhập/chi tiêu trong tháng này
        monthly_income = Transaction.objects.filter(
            user=self.request.user, 
            transaction_type='income',
            date__gte=start_month
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        monthly_expense = Transaction.objects.filter(
            user=self.request.user, 
            transaction_type='expense',
            date__gte=start_month
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        monthly_balance = monthly_income - monthly_expense
        
        # Lấy danh sách thẻ/ví
        cards = Card.objects.filter(user=self.request.user)
        
        # Lấy các mục tiêu đang thực hiện
        goals = Goal.objects.filter(
            user=self.request.user,
            status='in_progress'
        ).order_by('-end_date')[:5]
        
        context.update({
            'monthly_income': monthly_income,
            'monthly_expense': monthly_expense,
            'monthly_balance': monthly_balance,
            'cards': cards,
            'goals': goals,
        })
        
        return context

@login_required
def goal_contribute(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', 0))
            card_id = request.POST.get('card')
            
            if amount <= 0:
                messages.error(request, 'Số tiền đóng góp phải lớn hơn 0')
                return redirect('finance_app:goal-list')
                
            card = get_object_or_404(Card, pk=card_id, user=request.user)
            
            if card.balance < amount:
                messages.error(request, 'Số dư trong thẻ/ví không đủ')
                return redirect('finance_app:goal-list')
            
            # Tạo giao dịch thu nhập
            Transaction.objects.create(
                user=request.user,
                amount=amount,
                transaction_type='income',
                date=timezone.now().date(),
                card=card,
                note=f'Đóng góp vào mục tiêu: {goal.name}'
            )
            
            # Cập nhật số dư thẻ/ví
            card.balance -= amount
            card.save()
            
            messages.success(request, f'Đã đóng góp {amount|intcomma} VND vào mục tiêu {goal.name}')
            
        except (ValueError, TypeError):
            messages.error(request, 'Số tiền không hợp lệ')
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
            
    return redirect('finance_app:goal-list')

class GoalContributionView(LoginRequiredMixin, View):
    def get(self, request, pk):
        goal = get_object_or_404(Goal, pk=pk, user=request.user)
        form = GoalContributionForm(user=request.user, goal=goal)
        context = {
            'goal': goal,
            'form': form,
            'remaining_amount': goal.target_amount - goal.current_amount
        }
        return render(request, 'finance_app/goal_contribution.html', context)
    
    def post(self, request, pk):
        goal = get_object_or_404(Goal, pk=pk, user=request.user)
        form = GoalContributionForm(user=request.user, goal=goal, data=request.POST)
        
        if form.is_valid():
            expense_transaction = None
            goal_transaction = None
            try:
                with transaction.atomic():
                    # Lấy dữ liệu từ form
                    amount = form.cleaned_data['amount']
                    card = form.cleaned_data['card']
                    note = form.cleaned_data['note']
                    
                    # Tìm hoặc tạo danh mục Tiết kiệm
                    saving_category, created = Category.objects.get_or_create(
                        user=request.user,
                        name='Tiết kiệm',
                        defaults={
                            'type': 'expense',
                            'description': 'Danh mục cho các khoản tiết kiệm'
                        }
                    )
                    
                    # Tạo giao dịch trừ tiền từ thẻ/ví
                    expense_transaction = Transaction.objects.create(
                        user=request.user,
                        amount=amount,
                        transaction_type='expense',
                        card=card,
                        category=saving_category,
                        note=note or f'Thêm tiền vào mục tiêu {goal.name}',
                        date=timezone.now().date()
                    )
                    
                    # Lưu giao dịch mục tiêu
                    goal_transaction = GoalTransaction.objects.create(
                        goal=goal,
                        user=request.user,
                        amount=amount,
                        card=card,
                        note=note or f'Thêm tiền vào mục tiêu {goal.name}',
                        date=timezone.now().date()
                    )
                    
                    # Cập nhật số dư thẻ/ví
                    card.balance -= amount
                    if card.balance < 0:
                        card.balance = 0
                    card.save()
                    
                    # Cập nhật số tiền đã tiết kiệm của mục tiêu
                    goal.current_amount += amount
                    if goal.current_amount >= goal.target_amount:
                        goal.status = 'completed'
                    goal.save()
                    
                    messages.success(
                        request, 
                        f'Đã thêm {amount:,.0f} đ vào mục tiêu {goal.name}. '
                        f'Số dư còn lại trong tài khoản {card.name}: {card.balance:,.0f} VNĐ'
                    )
                    
                    return redirect('finance_app:goal-detail', pk=goal.pk)
                    
            except Exception as e:
                # Nếu có lỗi, xóa các giao dịch đã tạo (nếu có)
                if expense_transaction:
                    expense_transaction.delete()
                if goal_transaction:
                    goal_transaction.delete()
                messages.error(request, f'Có lỗi xảy ra: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{form.fields[field].label}: {error}')
        
        context = {
            'goal': goal,
            'form': form,
            'remaining_amount': goal.target_amount - goal.current_amount
        }
        return render(request, 'finance_app/goal_contribution.html', context)

@login_required
@require_POST
def toggle_category_default(request, category_id):
    """Toggle trạng thái mặc định của danh mục"""
    if not request.user.is_superuser:
        return JsonResponse({
            'success': False,
            'message': 'Bạn không có quyền thực hiện thao tác này'
        }, status=403)
    
    try:
        category = Category.objects.get(id=category_id, user=request.user)
        data = json.loads(request.body)
        category.is_default = data.get('is_default', False)
        category.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Đã {"đánh dấu" if category.is_default else "bỏ đánh dấu"} danh mục mặc định'
        })
    except Category.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Không tìm thấy danh mục'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'finance_app/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Không đánh dấu tất cả thông báo là đã đọc để dễ debug
        # self.get_queryset().update(is_read=True)
        return context

@login_required
def mark_notification_read(request, notification_id):
    if request.method == 'POST':
        try:
            notification = Notification.objects.get(id=notification_id, user=request.user)
            notification.is_read = True
            notification.save()
            return JsonResponse({'success': True})
        except Notification.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Không tìm thấy thông báo'})
    return JsonResponse({'success': False, 'message': 'Phương thức không hợp lệ'})

@login_required
def get_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    data = {
        'notifications': [
            {
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'type': n.notification_type,
                'created_at': n.created_at.strftime('%d/%m/%Y %H:%M'),
                'is_read': n.is_read
            } for n in notifications
        ],
        'unread_count': unread_count
    }
    
    return JsonResponse(data)

def create_notification(users, title, message, notification_type='system'):
    """
    Tạo thông báo cho một hoặc nhiều người dùng
    :param users: Một user hoặc một list các user
    :param title: Tiêu đề thông báo
    :param message: Nội dung thông báo
    :param notification_type: Loại thông báo (system, transaction, goal, budget)
    """
    # Đảm bảo users là list (dù là 1 user hay nhiều user)
    if not isinstance(users, (list, tuple)):
        users = [users]
    
    print(f"Đang tạo thông báo: {title} - {message}")
    print(f"Người nhận: {[user.username for user in users]}")
    
    for user in users:
        try:
            notification = Notification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type,
                is_read=False
            )
            print(f"Đã tạo thông báo ID: {notification.id} cho {user.username}")
        except Exception as e:
            print(f"Lỗi khi tạo thông báo cho {user.username}: {str(e)}")
    
    print("Hoàn thành tạo thông báo")

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'registration/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        # Thêm form vào context
        context['form'] = UserProfileForm()
        
        # Tạo hoặc lấy đối tượng UserProfile của người dùng
        user_profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        context['user_profile'] = user_profile
        
        return context
    
    def post(self, request, *args, **kwargs):
        user = request.user
        
        # Xử lý form cập nhật thông tin cá nhân
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email', '')
        
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if email:
            user.email = email
        
        user.save()
        
        # Xử lý form tải lên ảnh đại diện
        if 'avatar' in request.FILES:
            user_profile, created = UserProfile.objects.get_or_create(user=user)
            form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
            if form.is_valid():
                form.save()
                messages.success(request, 'Ảnh đại diện đã được cập nhật thành công!')
            else:
                for error in form.errors['avatar']:
                    messages.error(request, f'Lỗi: {error}')
        else:
            messages.success(request, 'Thông tin cá nhân đã được cập nhật thành công!')
        
        return redirect('profile')

class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'finance_app/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Transaction.objects.filter(user=self.request.user)
        
        # Lọc theo loại giao dịch
        transaction_type = self.request.GET.get('type')
        if transaction_type in ['income', 'expense']:
            queryset = queryset.filter(transaction_type=transaction_type)
            
        # Lọc theo danh mục
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
            
        # Lọc theo thẻ/ví
        card_id = self.request.GET.get('card')
        if card_id:
            queryset = queryset.filter(card_id=card_id)
            
        # Lọc theo khoảng thời gian
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Tìm kiếm theo ghi chú hoặc số tiền
        search = self.request.GET.get('search')
        if search:
            # Tìm kiếm theo ghi chú
            try:
                # Thử chuyển đổi search thành số để tìm theo amount
                amount = float(search.replace(',', ''))
                queryset = queryset.filter(
                    Q(note__icontains=search) | Q(amount=amount)
                )
            except (ValueError, TypeError):
                # Nếu không chuyển đổi được, chỉ tìm theo ghi chú
                queryset = queryset.filter(note__icontains=search)
        
        # Sắp xếp kết quả
        sort_by = self.request.GET.get('sort', '-date')
        if sort_by in ['-date', 'date', '-amount', 'amount']:
            queryset = queryset.order_by(sort_by, '-created_at')
        else:
            queryset = queryset.order_by('-date', '-created_at')
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(user=self.request.user)
        context['cards'] = Card.objects.filter(user=self.request.user)
        
        # Thêm các tham số lọc vào context
        context['selected_type'] = self.request.GET.get('type', '')
        context['selected_category'] = self.request.GET.get('category', '')
        context['selected_card'] = self.request.GET.get('card', '')
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        context['search'] = self.request.GET.get('search', '')
        context['sort'] = self.request.GET.get('sort', '-date')
        
        return context

class TransactionCreateView(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'finance_app/transaction_form.html'
    success_url = reverse_lazy('finance_app:transaction-list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        
        # Kiểm tra số dư trước khi lưu
        try:
            # Thử kiểm tra số dư
            if form.instance.transaction_type == 'expense':
                card = form.instance.card
                if card.balance < form.instance.amount:
                    # Tính số tiền thiếu
                    missing_amount = form.instance.amount - card.balance
                    # Thông báo chi tiết
                    error_message = f'Số dư không đủ để thực hiện giao dịch. Số dư hiện tại: {int(card.balance):,} VNĐ, cần thêm: {int(missing_amount):,} VNĐ'
                    form.add_error(None, error_message)
                    return self.form_invalid(form)
                    
            # Lưu giao dịch
            response = super().form_valid(form)
            
            # Cập nhật số dư thẻ/ví
            card = form.instance.card
            if form.instance.transaction_type == 'income':
                card.balance += form.instance.amount
            else:  # expense
                card.balance -= form.instance.amount
                if card.balance < 0:
                    card.balance = 0
            card.save()
            
            # Tạo thông báo
            transaction_type = 'Thu nhập' if form.instance.transaction_type == 'income' else 'Chi tiêu'
            create_notification(
                self.request.user,
                f'Giao dịch {transaction_type} mới',
                f'Bạn đã tạo một giao dịch {transaction_type.lower()}: {form.instance.amount:,.0f} VNĐ - {form.instance.category.name}',
                'transaction'
            )
            
            return response
            
        except ValidationError as e:
            # Bắt lỗi ValidationError và hiển thị trên form
            form.add_error(None, str(e))
            return self.form_invalid(form)

class TransactionDetailView(LoginRequiredMixin, DetailView):
    model = Transaction
    template_name = 'finance_app/transaction_detail.html'
    context_object_name = 'transaction'
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transaction = self.object
        
        # Thêm thông tin bổ sung về giao dịch
        context['transaction_type_display'] = transaction.get_transaction_type_display()
        
        # Lấy các giao dịch liên quan (cùng danh mục)
        related_transactions = Transaction.objects.filter(
            user=self.request.user,
            category=transaction.category
        ).exclude(id=transaction.id).order_by('-date')[:5]
        
        context['related_transactions'] = related_transactions
        
        return context

class TransactionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'finance_app/transaction_form.html'
    success_url = reverse_lazy('finance_app:transaction-list')
    
    def test_func(self):
        transaction = self.get_object()
        return transaction.user == self.request.user
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        # Lấy thông tin giao dịch cũ trước khi cập nhật
        old_transaction = self.get_object()
        old_amount = old_transaction.amount
        old_type = old_transaction.transaction_type
        old_card = old_transaction.card
        
        # Hoàn trả số dư cho thẻ/ví cũ
        if old_type == 'income':
            old_card.balance -= old_amount
        else:  # expense
            old_card.balance += old_amount
        old_card.save()
        
        # Cập nhật giao dịch
        response = super().form_valid(form)
        
        # Cập nhật số dư thẻ/ví mới
        new_card = form.instance.card
        if form.instance.transaction_type == 'income':
            new_card.balance += form.instance.amount
        else:  # expense
            new_card.balance -= form.instance.amount
            if new_card.balance < 0:
                new_card.balance = 0
        new_card.save()
        
        # Tạo thông báo
        transaction_type = 'Thu nhập' if form.instance.transaction_type == 'income' else 'Chi tiêu'
        create_notification(
            self.request.user,
            f'Cập nhật giao dịch {transaction_type}',
            f'Bạn đã cập nhật giao dịch {transaction_type.lower()}: {form.instance.amount:,.0f} VNĐ - {form.instance.category.name}',
            'transaction'
        )
        
        return response

class TransactionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Transaction
    template_name = 'finance_app/transaction_confirm_delete.html'
    success_url = reverse_lazy('finance_app:transaction-list')
    
    def test_func(self):
        transaction = self.get_object()
        return transaction.user == self.request.user
    
    def delete(self, request, *args, **kwargs):
        transaction = self.get_object()
        
        try:
            # Lấy thông tin giao dịch trước khi xóa
            amount = transaction.amount
            transaction_type = transaction.transaction_type
            category_name = transaction.category.name if transaction.category else "Không danh mục"
            card = transaction.card
            transaction_date = transaction.date
            
            # Thêm lệnh print để debug
            print(f"Đang tạo thông báo xóa giao dịch: {amount} VND - {category_name}")
            
            with transaction.atomic():
                # Cập nhật số dư thẻ/ví
                if transaction_type == 'income':
                    card.balance -= amount
                    if card.balance < 0:
                        card.balance = 0
                else:  # expense
                    card.balance += amount
                card.save()
                
                # Tạo thông báo
                transaction_type_display = 'Thu nhập' if transaction_type == 'income' else 'Chi tiêu'
                create_notification(
                    request.user,
                    f'Xóa giao dịch {transaction_type_display}',
                    f'Giao dịch {transaction_type_display.lower()} ({amount:,.0f} VNĐ - {category_name}) đã được xóa',
                    'transaction'
                )
                
                # Thêm lệnh print để xác nhận thông báo đã được tạo
                print("Đã tạo thông báo xóa giao dịch")
                
                return super().delete(request, *args, **kwargs)
                
        except Exception as e:
            print(f"Lỗi khi xóa giao dịch: {str(e)}")
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
            return redirect('finance_app:transaction-list')
        

# Trang đăng xuất tùy chỉnh
class CustomLogoutView(View):
    def get(self, request, *args, **kwargs):
        # Đăng xuất người dùng
        logout(request)
        # Chuyển hướng đến trang landing
        return redirect('finance_app:landing')
    
    def post(self, request, *args, **kwargs):
        # Đăng xuất người dùng khi sử dụng phương thức POST
        logout(request)
        # Chuyển hướng đến trang landing
        return redirect('finance_app:landing')

@login_required
@user_passes_test(is_admin)
def export_users_to_excel(request):
    try:
        # Tạo một BytesIO object để lưu file Excel
        output = BytesIO()
        
        # Tạo workbook và worksheet
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Danh sách người dùng')
        
        # Định dạng cho header
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # Định dạng cho dữ liệu
        data_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        
        # Định dạng cho trạng thái
        active_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'fg_color': '#C6EFCE'
        })
        
        inactive_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'fg_color': '#FFC7CE'
        })
        
        # Đặt độ rộng cột
        worksheet.set_column('A:A', 20)  # Tên đăng nhập
        worksheet.set_column('B:B', 30)  # Email
        worksheet.set_column('C:C', 20)  # Ngày tham gia
        worksheet.set_column('D:D', 15)  # Số giao dịch
        worksheet.set_column('E:E', 15)  # Số ví/thẻ
        worksheet.set_column('F:F', 15)  # Số mục tiêu
        worksheet.set_column('G:G', 20)  # Trạng thái
        
        # Thêm header
        headers = ['Tên đăng nhập', 'Email', 'Ngày tham gia', 'Số giao dịch', 'Số ví/thẻ', 'Số mục tiêu', 'Trạng thái']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Lấy dữ liệu người dùng
        users = User.objects.all()
        row = 1
        
        for user in users:
            # Đếm số lượng giao dịch, ví/thẻ và mục tiêu
            transaction_count = Transaction.objects.filter(user=user).count()
            card_count = Card.objects.filter(user=user).count()
            goal_count = Goal.objects.filter(user=user).count()
            
            # Ghi dữ liệu vào worksheet
            worksheet.write(row, 0, user.username, data_format)
            worksheet.write(row, 1, user.email, data_format)
            worksheet.write(row, 2, user.date_joined.strftime('%d/%m/%Y %H:%M'), data_format)
            worksheet.write(row, 3, transaction_count, data_format)
            worksheet.write(row, 4, card_count, data_format)
            worksheet.write(row, 5, goal_count, data_format)
            
            # Ghi trạng thái với định dạng tương ứng
            status = 'Đang hoạt động' if user.is_active else 'Bị khóa'
            status_format = active_format if user.is_active else inactive_format
            worksheet.write(row, 6, status, status_format)
            
            row += 1
        
        # Thêm thông tin tổng kết
        worksheet.write(row + 1, 0, 'Tổng số người dùng:', header_format)
        worksheet.write(row + 1, 1, users.count(), data_format)
        worksheet.write(row + 2, 0, 'Người dùng đang hoạt động:', header_format)
        worksheet.write(row + 2, 1, users.filter(is_active=True).count(), data_format)
        worksheet.write(row + 3, 0, 'Người dùng bị khóa:', header_format)
        worksheet.write(row + 3, 1, users.filter(is_active=False).count(), data_format)
        
        # Đóng workbook
        workbook.close()
        
        # Tạo response
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=danh_sach_nguoi_dung_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        messages.success(request, 'Đã xuất danh sách người dùng thành công!')
        return response
        
    except Exception as e:
        messages.error(request, f'Có lỗi xảy ra khi xuất Excel: {str(e)}')
        return redirect('finance_app:admin-user-list')

@login_required
def update_profile(request):
    if request.method == 'POST':
        try:
            user = request.user
            profile = user.profile

            # Cập nhật thông tin User
            old_username = user.username
            old_email = user.email
            
            # Lấy dữ liệu từ form
            username = request.POST.get('username', '')
            email = request.POST.get('email', '')
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            
            if username and username != old_username:
                # Kiểm tra xem username đã tồn tại chưa
                if User.objects.filter(username=username).exclude(id=user.id).exists():
                    return JsonResponse({
                        'success': False,
                        'message': 'Tên đăng nhập đã tồn tại, vui lòng chọn tên đăng nhập khác'
                    })
                user.username = username
                
            if email and email != old_email:
                # Kiểm tra xem email đã tồn tại chưa
                if User.objects.filter(email=email).exclude(id=user.id).exists():
                    return JsonResponse({
                        'success': False,
                        'message': 'Email đã tồn tại, vui lòng sử dụng email khác'
                    })
                user.email = email
            
            # Cập nhật first_name và last_name
            user.first_name = first_name
            user.last_name = last_name
            
            user.save()

            # Tạo thông báo đơn giản
            create_notification(
                user,
                'Cập nhật thông tin tài khoản',
                'Bạn đã cập nhật thông tin tài khoản thành công',
                'system'
            )

            return JsonResponse({
                'success': True,
                'message': 'Bạn đã cập nhật thông tin thành công'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Có lỗi xảy ra: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Phương thức không được hỗ trợ'
    })

@login_required
def sync_profile_from_google(request):
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Phương thức không được hỗ trợ'
        })
    
    try:
        # Kiểm tra xem người dùng có liên kết với tài khoản Google không
        from allauth.socialaccount.models import SocialAccount
        social_accounts = SocialAccount.objects.filter(user=request.user, provider='google')
        
        if not social_accounts.exists():
            return JsonResponse({
                'success': False,
                'message': 'Tài khoản của bạn chưa được liên kết với Google'
            })
        
        # Lấy tài khoản Google đầu tiên
        social_account = social_accounts.first()
        extra_data = social_account.extra_data
        
        # Log thông tin để debug
        print(f"Google account extra data: {extra_data}")
        
        # Cập nhật thông tin người dùng
        user = request.user
        
        # Cập nhật email
        if 'email' in extra_data:
            user.email = extra_data['email']
        
        # Cập nhật họ tên
        if 'given_name' in extra_data:
            user.first_name = extra_data['given_name']
        if 'family_name' in extra_data:
            user.last_name = extra_data['family_name']
        
        # Lưu thay đổi
        user.save()
        
        # Tạo thông báo
        create_notification(
            user,
            'Đồng bộ thông tin từ Google',
            'Thông tin tài khoản của bạn đã được đồng bộ từ Google thành công',
            'system'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Đã đồng bộ thông tin từ Google thành công'
        })
    except Exception as e:
        print(f"Lỗi khi đồng bộ từ Google: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Có lỗi xảy ra: {str(e)}'
        })