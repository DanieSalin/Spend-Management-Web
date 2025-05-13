from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'finance_app'

urlpatterns = [
    # Đăng ký và đăng nhập
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    # path('logout/', auth_views.LogoutView.as_view(next_page='/', http_method_names=['get', 'post']), name='logout'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    # Quản lý tài khoản
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='registration/password_change.html',
        success_url='password_change_done'
    ), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='registration/password_change_done.html'
    ), name='password_change_done'),
    # Thêm dòng này vào urlpatterns trong personal_finance/urls.py
    path('accounts/logout/', views.CustomLogoutView.as_view(), name='custom_logout'),
    # Trang chủ và Dashboard
    path('', views.LandingView.as_view(), name='landing'),  # Trang giới thiệu
    path('home/', views.HomeView.as_view(), name='index'),  # Trang chủ sau khi đăng nhập
    # path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    
    # Quản lý danh mục
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category-create'),
    path('categories/<int:pk>/update/', views.CategoryUpdateView.as_view(), name='category-update'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category-delete'),
    path('categories/sync/', views.sync_default_categories, name='sync-categories'),
    path('api/categories/<int:pk>/toggle-default/', views.toggle_default_category, name='toggle-default-category'),
    
    # Quản lý thẻ
    path('cards/', views.CardListView.as_view(), name='card-list'),
    path('cards/add/', views.CardCreateView.as_view(), name='card-create'),
    path('cards/<int:pk>/update/', views.CardUpdateView.as_view(), name='card-update'),
    path('cards/<int:pk>/delete/', views.CardDeleteView.as_view(), name='card-delete'),
    
    # Quản lý mục tiêu
    path('goals/', views.GoalListView.as_view(), name='goal-list'),
    path('goals/add/', views.GoalCreateView.as_view(), name='goal-create'),
    path('goals/<int:pk>/update/', views.GoalUpdateView.as_view(), name='goal-update'),
    path('goals/<int:pk>/delete/', views.GoalDeleteView.as_view(), name='goal-delete'),
    path('goals/<int:pk>/contribute/', views.GoalContributionView.as_view(), name='goal-contribute'),
    path('goals/<int:pk>/', views.GoalDetailView.as_view(), name='goal-detail'),
    
    # Quản lý ngân sách
    path('budgets/', views.BudgetListView.as_view(), name='budget-list'),
    path('budgets/add/', views.BudgetCreateView.as_view(), name='budget-create'),
    path('budgets/<int:pk>/update/', views.BudgetUpdateView.as_view(), name='budget-update'),
    path('budgets/<int:pk>/delete/', views.BudgetDeleteView.as_view(), name='budget-delete'),
    
    # Quản lý giao dịch
    path('transactions/', views.TransactionListView.as_view(), name='transaction-list'),
    path('transactions/create/', views.TransactionCreateView.as_view(), name='transaction-create'),
    path('transactions/<int:pk>/', views.TransactionDetailView.as_view(), name='transaction-detail'),
    path('transactions/<int:pk>/update/', views.TransactionUpdateView.as_view(), name='transaction-update'),
    path('transactions/<int:pk>/delete/', views.TransactionDeleteView.as_view(), name='transaction-delete'),
    
    # Thống kê
    path('statistics/', views.statistics_view, name='statistics'),
    path('api/monthly-trend/', views.get_monthly_trend, name='api-monthly-trend'),
    
    # Thông báo
    path('notifications/', views.NotificationListView.as_view(), name='notification_list'),
    path('notifications/get/', views.get_notifications, name='get_notifications'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    
    # Admin URLs
    path('admin/', views.admin_dashboard, name='admin-dashboard'),
    path('admin/users/', views.admin_user_list, name='admin-user-list'),
    path('admin/users/<int:user_id>/', views.admin_user_detail, name='admin-user-detail'),
    path('admin/users/<int:user_id>/transactions/', views.admin_user_transactions, name='admin-user-transactions'),
    path('admin/users/<int:user_id>/toggle-status/', views.admin_toggle_user_status, name='admin-toggle-user-status'),
    path('admin/users/<int:user_id>/delete/', views.admin_delete_user, name='admin-delete-user'),
]