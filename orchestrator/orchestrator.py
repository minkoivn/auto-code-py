# orchestrator/orchestrator.py
import os
import subprocess
import json

# --- MOCK AI FUNCTIONS (GIẢ LẬP AI) ---

def mock_invoke_ai_x():
    """
    Giả lập AI X.
    Hàm này không gọi API thật mà tạo ra một bản vá (diff) được lập trình sẵn.
    Nó sẽ đề xuất thêm một dòng `print` vào file app/main.py.
    """
    print("🤖 [AI X] Đang phân tích mã nguồn và tạo đề xuất...")
    # Đây là nội dung của bản vá (diff)
    diff_content = """diff --git a/app/main.py b/app/main.py
index 4e1b9b1..20f6b3b 100644
--- a/app/main.py
+++ b/app/main.py
@@ -4,6 +4,7 @@
     Hiện tại nó chỉ in ra một thông điệp.
     """
     print("Hello from Project A - Version 1")
+    print("✨ AI was here and added this line! ✨")
 
 if __name__ == "__main__":
     run_application()

"""
    print("🤖 [AI X] Đã tạo xong đề xuất.")
    return diff_content

def mock_invoke_ai_y(diff):
    """
    Giả lập AI Y.
    Luôn luôn chấp thuận thay đổi cho mục đích demo.
    """
    print("🧐 [AI Y] Đang kiểm duyệt thay đổi...")
    print("🧐 [AI Y] Thay đổi hợp lệ!")
    return {
      "decision": "approved",
      "reason": "Demo change approved for local testing."
    }

# --- IMPLEMENTER FUNCTION (THỰC THI) ---

def execute_z_commit_and_push(diff, reason):
    """
    Áp dụng bản vá, commit thay đổi.
    Trong demo này, chúng ta không push lên server từ xa.
    """
    print("🚀 [Z] Bắt đầu quá trình thực thi...")
    patch_file = "change.patch"
    with open(patch_file, "w") as f:
        f.write(diff)

    try:
        # Áp dụng bản vá
        subprocess.run(["git", "apply", patch_file], check=True)
        print("🚀 [Z] Áp dụng bản vá thành công.")

        # Add file đã thay đổi vào staging
        subprocess.run(["git", "add", "app/main.py"], check=True)

        # Tạo commit
        commit_message = f"feat(AI): {reason}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        print(f"🚀 [Z] Đã tạo commit mới với thông điệp: '{commit_message}'")

    finally:
        # Dọn dẹp file patch
        if os.path.exists(patch_file):
            os.remove(patch_file)

# --- MAIN WORKFLOW ---

def main():
    print("--- BẮT ĐẦU CHU TRÌNH TIẾN HÓA DEMO ---")
    
    # 1. AI X tạo đề xuất
    proposed_diff = mock_invoke_ai_x()
    
    # 2. AI Y kiểm duyệt
    review = mock_invoke_ai_y(proposed_diff)
    
    # 3. Z thực thi nếu được chấp thuận
    if review.get("decision") == "approved":
        execute_z_commit_and_push(proposed_diff, review.get("reason"))
    else:
        print("❌ Thay đổi đã bị từ chối.")
        
    print("--- KẾT THÚC CHU TRÌNH ---")

if __name__ == "__main__":
    main()