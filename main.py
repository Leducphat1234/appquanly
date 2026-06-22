import tkinter as tk
from tkinter import ttk
from views.diemdanh import DiemDanhTab
from views.hocphi import HocPhiTab
from views.nhanvien import NhanVienTab
from views.sukien import SuKienTab
from views.lichsu import LichSuTab
from database import Database
from const import HANPHI, HOCPHI, ICON_B64
import sys, os

# def resource_path(relative_path):
#     """ Lấy đường dẫn tuyệt đối đến tài nguyên, hỗ trợ PyInstaller """
#     if hasattr(sys, '_MEIPASS'):
#         return os.path.join(sys._MEIPASS, relative_path)
#     return os.path.join(os.path.abspath("."), relative_path)

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hệ thống Quản lý Lớp học")
        self.geometry("1000x650")
        
        # icon_path = resource_path(os.path.join("assets", "icon.ico"))
        # if os.path.exists(icon_path):
        #     try:
        #         self.wm_iconbitmap(icon_path)
        #     except Exception as e:
        #         print(f"Lỗi nạp icon: {e}")
        
        self.db = Database() # Khởi tạo database
        # Khởi tạo Notebook
        self.notebook = ttk.Notebook(self)
        # QUAN TRỌNG: Truyền self.db vào đây
        self.tab_diem_danh = DiemDanhTab(self.notebook, self.db)
        self.tab_hoc_phi = HocPhiTab(self.notebook, self.db)
        self.tab_nhan_vien = NhanVienTab(self.notebook, self.db)
        self.tab_lich_su = LichSuTab(self.notebook, self.db)
        # Tương tự cho các tab khác nếu cần dùng DB
        # Thêm các tab vào giao diện
        # Thêm vào Notebook
        self.notebook.add(self.tab_diem_danh, text="Điểm danh")
        self.notebook.add(self.tab_hoc_phi, text="Học phí")
        self.notebook.add(self.tab_nhan_vien, text="Quản lý lớp")
        self.notebook.add(self.tab_lich_su, text="Lịch sử vắng")
        
        self.notebook.pack(expand=True, fill='both', padx=5, pady=5)
        
        # if sys.platform == "win32": self.iconbitmap("assets/icon.ico")
        
        # --- ĐÂY LÀ CHÌA KHÓA ĐỂ ĐỒNG BỘ ---
        def on_tab_change(event):
            # Lấy tab đang được chọn hiện tại
            selected_tab_id = self.notebook.select()
            current_tab = self.notebook.nametowidget(selected_tab_id)
            
            # Nếu tab đó có hàm load_data, hãy gọi nó để làm mới dữ liệu
            if hasattr(current_tab, 'load_data'):
                current_tab.load_data()

        self.notebook.bind("<<NotebookTabChanged>>", on_tab_change)

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
