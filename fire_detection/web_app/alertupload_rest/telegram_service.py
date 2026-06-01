import requests
import os
from django.conf import settings

def send_telegram_alert(message, image_path=None, chat_id=None):
    """
    Gửi cảnh báo phát hiện cháy/khói đến Telegram.
    Hỗ trợ gửi hình ảnh bằng chứng đi kèm (sử dụng sendPhoto).
    Nếu gửi ảnh bị lỗi hoặc không cung cấp ảnh, tự động chuyển sang gửi tin nhắn văn bản thường.
    """
    # Lấy TOKEN của Bot từ settings Django, nếu không cấu hình thì dùng giá trị mặc định
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', 'YOUR_TELEGRAM_BOT_TOKEN')
    
    # Nếu không chỉ định chat_id cụ thể từ tham số truyền vào, lấy chat_id mặc định từ settings Django
    if not chat_id:
        chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', 'YOUR_TELEGRAM_CHAT_ID')
        
    # Kiểm tra xem cấu hình có còn để mặc định hay không
    if token == 'YOUR_TELEGRAM_BOT_TOKEN' or chat_id == 'YOUR_TELEGRAM_CHAT_ID':
        print("[Telegram Alert] Cảnh báo: Bạn chưa cấu hình TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID thực tế trong settings.py.")
        
    # Gửi ảnh kèm chú thích nếu có ảnh
    if image_path and os.path.exists(image_path):
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        try:
            with open(image_path, 'rb') as photo_file:
                files = {'photo': photo_file}
                data = {'chat_id': chat_id, 'caption': message}
                response = requests.post(url, data=data, files=files)
                if response.ok:
                    print(f"[Telegram Alert] Đã gửi ảnh cảnh báo và chú thích lên Telegram thành công tới Chat ID: {chat_id}!")
                    return response
                else:
                    print(f"[Telegram Alert] Lỗi phản hồi khi gửi ảnh qua Telegram API: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"[Telegram Alert] Lỗi ngoại lệ xảy ra khi gửi ảnh qua Telegram: {e}")
            
    # Phương án dự phòng (Fallback): Gửi tin nhắn text thường nếu không có ảnh hoặc gửi ảnh lỗi
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    params = {'chat_id': chat_id, 'text': message}
    try:
        response = requests.get(url, params=params)
        if response.ok:
            print(f"[Telegram Alert] Đã gửi tin nhắn cảnh báo dạng văn bản lên Telegram tới Chat ID: {chat_id}!")
            return response
        else:
            print(f"[Telegram Alert] Lỗi phản hồi khi gửi tin nhắn text qua Telegram API: {response.status_code} - {response.text}")
            return response
    except Exception as e:
        print(f"[Telegram Alert] Lỗi ngoại lệ khi gửi tin nhắn qua Telegram: {e}")
        return None
