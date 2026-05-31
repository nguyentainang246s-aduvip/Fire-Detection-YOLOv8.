# ==========================================
# KHU VỰC: QUẦY TIẾP KHÁCH & GỬI CẢNH BÁO (VIEWS)
# ==========================================
# File này xử lý toàn bộ logic tiếp nhận yêu cầu từ client (PyQt5)
# và phân công nhiệm vụ gửi cảnh báo (Email/SMS) chạy ngầm bằng Đa luồng.

from alertupload_rest.serializers import UploadAlertSerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.core.mail import send_mail, EmailMessage
from rest_framework.exceptions import ValidationError
from threading import Thread
from twilio.rest import Client

import re
from django.conf import settings
import os

# ==========================================
# 1. ĐỊNH NGHĨA ĐỘI SHIPPER (DECORATOR ĐA LUỒNG)
# ==========================================
# Bất kỳ hàm nào được gắn mác `@start_new_thread` sẽ được tự động
# tách ra một luồng riêng biệt để chạy ngầm dưới nền hệ thống (Thread).
# Điều này giúp Lễ tân (API chính) không bị tắc nghẽn, trả kết quả tức thời cho khách.
def start_new_thread(function):
    def decorator(*args, **kwargs):
        # Khởi tạo một luồng phụ mới (Thread), chỉ định mục tiêu chạy là 'function'
        t = Thread(target = function, args=args, kwargs=kwargs)
        # Thiết lập daemon = True giúp luồng phụ tự động tắt khi tiến trình chính dừng
        t.daemon = True
        # Bắt đầu kích nổ động cơ (Chạy song song luồng phụ)
        t.start()
    return decorator


# ==========================================
# 2. QUẦY TIẾP NHẬN API CHÍNH (LỄ TÂN)
# ==========================================
# Cổng nhận hình ảnh từ PyQt5. Chỉ nhận phương thức POST (nộp đồ)
# và bắt buộc khách phải trình diện Thẻ VIP (Token Authentication).
@api_view(['POST'])
@permission_classes((IsAuthenticated, )) # RÀO AN NINH: Bắt buộc phải có token xác thực hợp lệ
def post_alert(request):
    # Giao gói dữ liệu thô (chứa ảnh, vị trí, nơi nhận) cho anh Phiên dịch kiểm tra
    serializer = UploadAlertSerializer(data=request.data)

    # Nếu dữ liệu đúng chuẩn định dạng (có ảnh, định dạng hợp lệ...)
    if serializer.is_valid():
        # Cất ảnh vào kho (Lưu bản ghi vào Database sqlite3)
        serializer.save()
        
        # Gọi đội shipper chạy ngầm để nhận diện email/SĐT rồi gửi thư đi
        # Lễ tân chỉ cần đưa thông tin cần thiết rồi ném qua luồng phụ, không trực tiếp đứng chờ
        identify_email_sms(serializer)

    else:
        # Nếu gửi sai dữ liệu, đuổi khách bằng mã lỗi
        return "Error: Unable to process data!"

    # Trả về thành công ngay lập tức bằng token xác thực của khách (Tốc độ siêu tốc)
    return Response(request.META.get('HTTP_AUTHORIZATION'))


# ==========================================
# 3. MÁY QUÉT SINH TRẮC HỌC (NHẬN DIỆN LIÊN HỆ)
# ==========================================
# Hàm này dùng Regex để soi xem thông tin nơi nhận là Email hay Số điện thoại.
def identify_email_sms(serializer):

    # A. Nếu tìm thấy định dạng chuỗi chứa ký tự '@' và đuôi tên miền hợp lệ
    if(re.search(r'^[\w\.-]+@[\w\.-]+\.\w+$', serializer.data['alert_receiver'])):  
        print("Bảo vệ: Phát hiện đây là một EMAIL hợp lệ!")
        # Bàn giao cho Shipper chuyên gửi Email
        send_email(serializer)
        
    # B. Nếu khớp với định dạng bắt đầu bằng đầu số quốc gia +84 và 10 số tiếp theo
    elif re.compile("[+84][0-9]{10}").match(serializer.data['alert_receiver']):
        print("Bảo vệ: Phát hiện đây là một SỐ ĐIỆN THOẠI hợp lệ!")
        # Bàn giao cho Shipper chuyên gửi tin nhắn SMS Twilio
        send_sms(serializer)
        
    else:
        # Trường hợp khách cung cấp thông tin liên hệ không đúng chuẩn
        print("Bảo vệ: Thông tin nơi nhận không phải Email hay SĐT hợp lệ!")


# ==========================================
# 4. SHIPPER GỬI SMS QUA TWILIO (CHẠY NGẦM)
# ==========================================
# Sử dụng @start_new_thread để tách khỏi luồng chính
@start_new_thread
def send_sms(serializer):
    # Kết nối cổng dịch vụ Twilio bằng tài khoản và mã khóa lưu trong settings
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    # Tạo và phóng tin nhắn SMS gửi tới điện thoại của khách
    message = client.messages.create(body=prepare_alert_message(serializer),
                                    from_=settings.TWILIO_NUMBER,
                                    to=serializer.data['alert_receiver'])


# ==========================================
# 5. SHIPPER GỬI EMAIL SMTP GMAIL (CHẠY NGẦM)
# ==========================================
# Sử dụng @start_new_thread để chạy song song ngầm phía sau
@start_new_thread
def send_email(serializer):
    
    subject = 'Fire/Smoke Detected! [CẢNH BÁO CHÁY]'
    # Soạn thảo thư thông báo chi tiết
    message = prepare_alert_message(serializer) 
    # Khởi tạo hòm thư gửi đi: Tiêu đề, Nội dung, Email gửi (settings), Email nhận
    email = EmailMessage(subject, message, settings.EMAIL_HOST_USER, [serializer.data['alert_receiver']])
    
    # === XỬ LÝ ĐÍNH KÈM TỆP ẢNH ===
    # Lấy thông tin đường dẫn ảnh vừa lưu
    image_value = str(serializer.data.get('image', ''))
    filename = image_value.split('/')[-1] # Tách lấy tên file ảnh (ví dụ: alert.jpg)
    image_path = os.path.join(settings.MEDIA_ROOT, filename) # Khớp nối với đường dẫn vật lý thực tế trên đĩa cứng
    print("Đang tìm ảnh tại đĩa cứng:", image_path)
 
    try:
        # Đọc dữ liệu nhị phân của ảnh ('rb') để đính kèm vào thư
        with open(image_path, 'rb') as image_file:
            email.attach(filename='detection.jpg', content=image_file.read(), mimetype='image/jpeg')

        # Ra lệnh gửi thư bằng dịch vụ Gmail SMTP
        email.send(fail_silently=False)
        print("Đã gửi email cảnh báo đính kèm ảnh thành công!")
        
    except Exception as e:
        # PHƯƠNG ÁN DỰ PHÒNG AN TOÀN:
        # Nếu luồng phụ không tìm thấy tệp ảnh hoặc lỗi kết nối, hệ thống vẫn
        # cố gắng gửi một email bằng chữ (không kèm ảnh) để khách vẫn nhận được cảnh báo!
        print(f"Lỗi khi gửi email có đính kèm: {e}")  
        try:
            email_no_img = EmailMessage(subject, message, settings.EMAIL_HOST_USER, [serializer.data['alert_receiver']])
            email_no_img.send(fail_silently=False)
            print("Đã gửi email khẩn cấp thành công (không có đính kèm ảnh).")
        except Exception as ex:
            # Ghi nhận lỗi hoàn toàn nếu bưu điện sập hoặc cấu hình sai tài khoản Gmail
            print(f"Lỗi gửi email hoàn toàn: {ex}")


# ==========================================
# 6. BỘ SOẠN THẢO THƯ (PREPARE MESSAGE)
# ==========================================
# Tạo thông điệp cảnh báo chứa liên kết dẫn trực tiếp tới trang chi tiết của vụ báo cháy
def prepare_alert_message(serializer):
    # Cắt lấy ID/tên ảnh của vụ cháy
    uuid_with_slashes = split(serializer.data['image'], ".")
    uuid = uuid_with_slashes[0].lstrip('/')

    print("uuid ảnh: ", uuid)
    # Đường link chi tiết vụ cháy trên trang web
    url = 'http://127.0.0.1:8000/alerts/' + uuid
    print("Đường dẫn xem chi tiết: ", url)
    return '\nPhát hiện cháy/khói! \nXem chi tiết hình ảnh cảnh báo tại: ' + url


# Helper hỗ trợ phân tách chuỗi ký tự
def split(value, key):
    return str(value).split(key)