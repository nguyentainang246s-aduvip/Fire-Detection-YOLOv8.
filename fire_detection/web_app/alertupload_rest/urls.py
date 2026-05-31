from rest_framework import routers
from . import views
from rest_framework.authtoken import views as rest_framework_views
from django.urls import path, include, re_path

# ==========================================
# KHU VỰC: BẢNG CHỈ ĐƯỜNG API (URL ROUTING)
# ==========================================
# Bảng chỉ đường giúp Django điều phối luồng giao thông mạng.
# Khi có khách quốc tế truy cập vào các đường dẫn API tương ứng,
# hệ thống sẽ dẫn họ tới đúng nhân viên/quầy tiếp khách để xử lý.
urlpatterns = [
    # 1. Quầy tiếp nhận nộp ảnh báo cháy gửi từ PyQt5
    # Đường dẫn thực tế: /api/images/
    path('images/', views.post_alert, name='post_alert'),

    # 2. Quầy Lễ Tân chuyên cấp phát Thẻ VIP (Token Authentication) của DRF
    # Đường dẫn thực tế: /api/get_auth_token/
    # Khách gửi kèm Username/Password hợp lệ thì sẽ nhận được mã Token đặc quyền.
    re_path(r'^get_auth_token/$', rest_framework_views.obtain_auth_token, name='get_auth_token'),
]