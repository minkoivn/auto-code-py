# app/application.py
import time
import os

def run_app():
    """
    Đây là nơi chứa logic chính của ứng dụng của bạn.
    """
    print(f"[{time.ctime()}] --- Ứng dụng đang chạy (PID: {os.getpid()}) --- Phiên bản 1.0")
    
    # Để kiểm tra, hãy thử thay đổi nội dung của tệp này khi nó đang chạy.
    # Ví dụ: thay đổi "Phiên bản 1.0" thành "Phiên bản 1.1" và lưu lại.
    # main.py sẽ tự động phát hiện và khởi động lại nó.
    
    # Để kiểm tra phục hồi lỗi, hãy tạo ra lỗi cú pháp và lưu lại.
    # Ví dụ: xóa dấu ngoặc ở cuối dòng print bên dưới.
    # print(f"Một dòng code không lỗi"
    
    count = 0
    while True:
        print(f"[{time.ctime()}] Tim đập... Lần thứ {count+1}")
        count += 1
        time.sleep(10)

if __name__ == "__main__":
    try:
        run_app()
    except Exception as e:
        # Ghi lỗi vào stderr để main.py có thể bắt được
        import sys
        print(f"Ứng dụng gặp lỗi và bị sập: {e}", file=sys.stderr)
        # Thoát với mã lỗi để báo hiệu cho supervisor
        sys.exit(1)