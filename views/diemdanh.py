import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from const import HANPHI, HOCPHI, FONTSIZE

class DiemDanhTab(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.today_str = datetime.now().strftime("%Y-%m-%d")
        self.class_options = []

        toolbar = ttk.Frame(self)
        toolbar.pack(fill='x', padx=10, pady=10)

        tk.Label(toolbar, text=f"NGÀY ĐIỂM DANH: {self.today_str}", font=("Arial", FONTSIZE, "bold")).pack(side='left', padx=10)
        self.class_filter = ttk.Combobox(toolbar, state='readonly', width=24)
        self.class_filter.pack(side='left', padx=10)
        self.class_filter.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        ttk.Button(toolbar, text="Làm mới", command=self.load_data).pack(side='right', padx=5)
        ttk.Button(toolbar, text="LƯU / CẬP NHẬT ĐIỂM DANH", command=self.cap_nhat_diem_danh).pack(side='left', padx=5)

        columns = ("stt", "name", "dob", "lop", "deadline", "diem_so", "ghi_chu", "attendance", "real_id")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        headers = [
            ("stt", "STT", 40),
            ("name", "Họ và Tên", 200),
            ("dob", "Năm sinh", 80),
            ("lop", "Lớp", 120),
            ("deadline", "Hạn học phí", 110),
            ("diem_so", "Điểm số", 80),
            ("ghi_chu", "Ghi chú", 260),
            ("attendance", "Vắng mặt", 90)
        ]
        for cid, txt, wid in headers:
            self.tree.heading(cid, text=txt)
            self.tree.column(cid, width=wid, anchor="center" if cid != "ghi_chu" else "w")

        self.tree.column("real_id", width=0, stretch=tk.NO)
        self.tree.pack(expand=True, fill='both', padx=10, pady=5)

        self.style = ttk.Style()
        self.style.configure("Treeview", font=("Arial", FONTSIZE), rowheight=28)
        self.style.configure("Treeview.Heading", font=("Arial", FONTSIZE, "bold"))

        self.tree.bind("<ButtonRelease-1>", self.on_tree_click)
        self.tree.bind("<Return>", self.toggle_attendance_by_key)
        self.tree.bind("<Button-3>", self.show_context_menu)

        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Chỉnh sửa", command=self.edit_student)
        self.context_menu.add_command(label="Đánh dấu VẮNG (Gia hạn +1 ngày)", command=self.mark_absent)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Xóa học viên", command=self.delete_student)

        self.load_class_filter()
        self.load_data()

    def toggle_attendance_by_key(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return

        item_id = selected_items[0]
        values = list(self.tree.item(item_id, 'values'))
        if values[0] == "+":
            return
        if values[7] == "☐":
            values[7] = "☑"
        else:
            values[7] = "☐"
        self.tree.item(item_id, values=values)
        self.tree.focus(item_id)
        self.tree.selection_set(item_id)

    def load_class_filter(self):
        self.class_options = [(-1, "Tất cả lớp")]
        self.class_options += self.db.get_all_lop_names()
        self.class_filter['values'] = [name for _, name in self.class_options]
        self.class_filter.current(0)

    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        class_id = self.class_options[self.class_filter.current()][0] if self.class_filter.current() >= 0 else -1
        if class_id == -1:
            self.db.cursor.execute("""
                SELECT hv.id, hv.ho_ten, hv.ngay_sinh, COALESCE(lp.ten_lop, 'Chưa phân lớp'), hv.han_hoc_phi,
                       COALESCE(hv.diem_so, 0), COALESCE(hv.ghi_chu, '')
                FROM hoc_vien hv
                LEFT JOIN lop lp ON hv.id_lop = lp.id
                ORDER BY lp.ten_lop, hv.ho_ten
            """)
        else:
            self.db.cursor.execute("""
                SELECT hv.id, hv.ho_ten, hv.ngay_sinh, COALESCE(lp.ten_lop, 'Chưa phân lớp'), hv.han_hoc_phi,
                       COALESCE(hv.diem_so, 0), COALESCE(hv.ghi_chu, '')
                FROM hoc_vien hv
                LEFT JOIN lop lp ON hv.id_lop = lp.id
                WHERE hv.id_lop = ?
                ORDER BY hv.ho_ten
            """, (class_id,))

        for stt, row in enumerate(self.db.cursor.fetchall(), start=1):
            real_id = row[0]
            trang_thai = self.db.get_trang_thai_hom_nay(real_id)
            icon = "☑" if trang_thai == "Vắng" else "☐"
            self.tree.insert("", tk.END, values=(stt, row[1], row[2], row[3], row[4], row[5], row[6], icon, real_id))
        self.tree.insert("", tk.END, values=("+", "--- Thêm học viên mới ---", "", "", "", "", "", "", ""))

    def on_tree_click(self, event):
        item_id = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if not item_id:
            return

        values = list(self.tree.item(item_id, 'values'))
        if values[0] == "+":
            self.open_add_student_window()
            return

        if column == "#8":
            values[7] = "☐" if values[7] == "☑" else "☑"
            self.tree.item(item_id, values=values)

    def cap_nhat_diem_danh(self):
        danh_sach_vang = []
        for item in self.tree.get_children():
            values = self.tree.item(item, 'values')
            if values[0] != "+" and values[7] == "☑":
                danh_sach_vang.append(values[8])
        self.db.luu_diem_danh_ngay(self.today_str, danh_sach_vang)
        messagebox.showinfo("Thành công", f"Đã lưu danh sách vắng ngày {self.today_str}")
        self.load_data()

    def show_context_menu(self, event):
        item_id = self.tree.identify_row(event.y)
        if item_id:
            self.tree.selection_set(item_id)
            if self.tree.item(item_id, 'values')[0] != "+":
                self.context_menu.post(event.x_root, event.y_root)

    def edit_student(self):
        selected = self.tree.selection()
        if not selected:
            return
        real_id = self.tree.item(selected[0], 'values')[8]
        self.open_add_student_window(edit_mode=True, student_id=real_id)

    def open_add_student_window(self, edit_mode=False, student_id=None):
        if hasattr(self, 'popup_win') and self.popup_win.winfo_exists():
            self.popup_win.destroy()

        self.popup_win = tk.Toplevel(self)
        self.popup_win.title("Chỉnh sửa" if edit_mode else "Thêm mới")
        self.popup_win.geometry("420x560")
        self.popup_win.grab_set()

        name_v, dob_v, deadline_v = "", "", (datetime.now() + timedelta(days=HANPHI)).strftime("%Y-%m-%d")
        fee_v, disc_v, lop_id, diem_so_v, ghi_chu_v = HOCPHI, 0, -1, 0, ""

        if edit_mode and student_id:
            self.db.cursor.execute("""
                SELECT ho_ten, ngay_sinh, han_hoc_phi, hoc_phi_goc, giam_gia, id_lop, COALESCE(diem_so, 0), COALESCE(ghi_chu, '')
                FROM hoc_vien WHERE id=?
            """, (student_id,))
            row = self.db.cursor.fetchone()
            if row:
                name_v, dob_v, deadline_v, fee_v, disc_v, lop_id, diem_so_v, ghi_chu_v = row

        fields = [
            ("Họ Tên:", name_v),
            ("Năm sinh:", dob_v),
            ("Hạn phí:", deadline_v),
            ("Học phí:", fee_v),
            ("Giảm (%):", disc_v),
            ("Điểm số:", diem_so_v),
            ("Ghi chú:", ghi_chu_v)
        ]
        self.entries = {}

        for label, val in fields:
            tk.Label(self.popup_win, text=label).pack(pady=(5, 0))
            ent = ttk.Entry(self.popup_win, width=36)
            ent.insert(0, str(val))
            ent.pack(pady=5)
            self.entries[label] = ent

        tk.Label(self.popup_win, text="Lớp học:").pack(pady=(6, 0))
        all_classes = self.db.get_all_lop_names()
        class_names = ["Chưa phân lớp"] + [name for _, name in all_classes]
        self.class_select = ttk.Combobox(self.popup_win, values=class_names, state='readonly', width=34)
        self.class_select.pack(pady=5)
        if lop_id and lop_id != -1:
            class_ids = [cid for cid, _ in all_classes]
            if lop_id in class_ids:
                self.class_select.current(class_ids.index(lop_id) + 1)
            else:
                self.class_select.current(0)
        else:
            self.class_select.current(0)

        def save():
            data = {k: v.get().strip() for k, v in self.entries.items()}
            if not data["Họ Tên:"]:
                messagebox.showwarning("Lỗi", "Vui lòng nhập tên học viên.")
                return
            try:
                selected_class_index = self.class_select.current()
                id_lop = None
                if selected_class_index > 0:
                    id_lop = all_classes[selected_class_index - 1][0]

                diem_so = float(data["Điểm số:"]) if data["Điểm số:"] else 0
                ghi_chu = data["Ghi chú:"]

                if edit_mode:
                    self.db.update_hoc_vien(
                        student_id,
                        data["Họ Tên:"],
                        data["Năm sinh:"],
                        data["Hạn phí:"],
                        float(data["Học phí:"]),
                        float(data["Giảm (%):"]),
                        id_lop,
                        diem_so,
                        ghi_chu
                    )
                else:
                    self.db.add_hoc_vien(
                        data["Họ Tên:"],
                        data["Năm sinh:"],
                        data["Hạn phí:"],
                        float(data["Học phí:"]),
                        float(data["Giảm (%):"]),
                        id_lop,
                        diem_so,
                        ghi_chu
                    )
                self.popup_win.destroy()
                self.load_data()
                self.load_class_filter()
            except ValueError:
                messagebox.showerror("Lỗi", "Học phí, Giảm giá và Điểm số phải là số!")

        ttk.Button(self.popup_win, text="LƯU", command=save).pack(pady=20)
        self.popup_win.bind('<Return>', lambda e: save())

    def delete_student(self):
        selected = self.tree.selection()
        if not selected:
            return
        vals = self.tree.item(selected[0], 'values')
        if messagebox.askyesno("Xác nhận", f"Xóa {vals[1]}?"):
            self.db.cursor.execute("DELETE FROM hoc_vien WHERE id=?", (vals[8],))
            self.db.conn.commit()
            self.load_data()

    def mark_absent(self):
        selected = self.tree.selection()
        if not selected:
            return
        vals = self.tree.item(selected[0], 'values')
        self.db.diem_danh_va_gia_han(vals[8], "Vắng")
        messagebox.showinfo("Xong", f"Đã vắng và gia hạn cho {vals[1]}")
        self.load_data()
