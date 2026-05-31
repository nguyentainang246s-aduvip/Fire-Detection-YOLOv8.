import sys
import traceback
import os

# Thêm dòng này để ngăn xung đột lõi (C++) giữa PyTorch (YOLO) và PyQt5
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

print("1. Đang khởi động chương trình...")

# Chúng ta sẽ đặt toàn bộ chương trình vào trong một khối try-except
# để bắt và hiển thị bất kỳ lỗi nào xảy ra khi khởi động.
try:
    print("-> Đang load Ultralytics (AI Model) TRƯỚC TIÊN...")
    from ultralytics import YOLO
    print("2. Đã load xong Ultralytics")

    print("-> Đang load PyQt5...")
    from PyQt5.QtWidgets import QApplication
    print("2.1 Đã load xong thư viện PyQt5")

    print("-> Đang load OpenCV...")
    import cv2
    print("2.2 Đã load xong OpenCV")

    print("-> Đang load Giao diện...")
    from login_window import LoginWindow
    print("3. Đã load xong các cửa sổ giao diện")

    # Bắt đầu ứng dụng
    app = QApplication(sys.argv)
    print("4. Đã khởi tạo QApplication")

    mainwindow = LoginWindow()
    print("5. Sẵn sàng hiển thị giao diện!")
    sys.exit(app.exec_())

except Exception as e:
    # Nếu có lỗi, in thông báo và chi tiết lỗi ra màn hình
    print("ĐÃ CÓ LỖI XẢY RA KHI KHỞI ĐỘNG ỨNG DỤNG:")
    traceback.print_exc()
    # Dòng này sẽ giữ cho cửa sổ Terminal không bị đóng ngay lập tức
    input("\nNhấn phím Enter để thoát...")