from rest_framework import serializers
from detection.models import UploadAlert

# ==========================================
# KHU VỰC: PHÒNG PHIÊN DỊCH (SERIALIZER)
# ==========================================
# Serializer đóng vai trò là "Thông dịch viên" cho mô hình UploadAlert.
# Nó nhận diện dữ liệu thô gửi lên (từ client/PyQt5), kiểm tra tính hợp lệ
# và dịch nó sang đối tượng Python để cất giữ vào Database.
# Ngược lại, nó cũng dịch hồ sơ từ database sang ngôn ngữ chung JSON để gửi trả khách.
class UploadAlertSerializer(serializers.ModelSerializer):

    class Meta:
        model = UploadAlert
        # Các cột thông tin (trường) cần dịch để lưu trữ/trả về
        # 'pk' (Mã số), 'image' (Đường dẫn ảnh), 'user_ID' (Chủ sở hữu token),
        # 'location' (Vị trí), 'date_created' (Thời gian tạo), 'alert_receiver' (Nơi nhận cảnh báo)
        fields = ('pk', 'image', 'user_ID', 'location', 'date_created', 'alert_receiver')