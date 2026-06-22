import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from const import FONTSIZE

class HocPhiTab(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db

        toolbar = ttk.Frame(self)
        toolbar.pack(fill='x', padx=10, pady=8)
        ttk.Button(toolbar, text="Làm mới", command=self.load_data).pack(side='right', padx=5)
        ttk.Button(toolbar, text="Xác nhận đóng phí", command=self.confirm_payment).pack(side='right', padx=5)

        self.tree = ttk.Treeview(self, columns=("stt", "ten", "lop", "goc", "giam", "thuc", "han", "tt", "id"), show="headings")
        cols = [("stt", "STT", 40), ("ten", "Học viên", 150), ("lop", "Lớp", 120), ("goc", "Học phí gốc", 100),
                ("giam", "Giảm", 60), ("thuc", "Thực thu", 100), ("han", "Hạn phí", 110), ("tt", "Trạng thái", 100)]
        for cid, txt, wid in cols:
            self.tree.heading(cid, text=txt)
            self.tree.column(cid, width=wid, anchor="center")
        self.tree.column("id", width=0, stretch=tk.NO)
        self.tree.pack(expand=True, fill='both', padx=10, pady=5)
        self.tree.tag_configure('late', foreground='red', font=('Arial', FONTSIZE, 'bold'))

        self.load_data()

    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.db.cursor.execute('''
            SELECT hv.id, hv.ho_ten, COALESCE(lp.ten_lop, 'Chưa phân lớp'), hv.han_hoc_phi,
                   hv.hoc_phi_goc, hv.giam_gia, hv.loai_giam_gia, hv.trang_thai_phi
            FROM hoc_vien hv
            LEFT JOIN lop lp ON hv.id_lop = lp.id
            ORDER BY lp.ten_lop, hv.ho_ten
        ''')
        students = self.db.cursor.fetchall()
        today = datetime.now().strftime("%Y-%m-%d")

        for stt, row in enumerate(students, start=1):
            sid, name, lop, deadline, base, disc, dtype, trang_thai = row
            final = base * (1 - disc/100) if dtype == "%" else max(0, base - disc)
            status = trang_thai
            tag = 'late' if deadline <= today and trang_thai != "Đã đóng" else ''
            self.tree.insert("", tk.END, values=(stt, name, lop, f"{base:,.0f}", f"{disc}{dtype}",
                                                   f"{final:,.0f}", deadline, status, sid), tags=(tag,))

    def confirm_payment(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Thông báo", "Vui lòng chọn học viên đóng phí")
            return
        values = self.tree.item(selected[0], 'values')
        real_id = values[8]
        name = values[1]
        if messagebox.askyesno("Xác nhận", f"Học viên {name} đã hoàn thành học phí?"):
            self.db.cap_nhat_dong_phi(real_id, "Đã đóng")
            self.load_data()
