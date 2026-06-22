import sqlite3
import os
from datetime import datetime
from const import HOCPHI

class Database:
    def __init__(self, db_name="sys_db/quan_li_lop_hoc.db"):
        os.makedirs("sys_db", exist_ok=True)
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self._migrate_schema()

    def column_exists(self, table, column):
        self.cursor.execute(f"PRAGMA table_info({table})")
        return any(row[1] == column for row in self.cursor.fetchall())

    def _migrate_schema(self):
        """Cập nhật schema từ cũ sang mới"""
        # Thêm cột tien_thuong nếu chưa có
        if not self.column_exists('giao_vien', 'tien_thuong'):
            self.cursor.execute("ALTER TABLE giao_vien ADD COLUMN tien_thuong REAL DEFAULT 0")
            self.conn.commit()
        if not self.column_exists('hoc_vien', 'diem_so'):
            self.cursor.execute("ALTER TABLE hoc_vien ADD COLUMN diem_so REAL DEFAULT 0")
            self.conn.commit()
        if not self.column_exists('hoc_vien', 'ghi_chu'):
            self.cursor.execute("ALTER TABLE hoc_vien ADD COLUMN ghi_chu TEXT DEFAULT ''")
            self.conn.commit()

    def create_tables(self):
        # Bảng giáo viên
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS giao_vien (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ho_ten TEXT NOT NULL,
                luong_mot_tiet REAL DEFAULT 0,
                tien_thuong REAL DEFAULT 0
            )
        ''')
        # Bảng lớp học
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS lop (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ten_lop TEXT NOT NULL UNIQUE,
                mo_ta TEXT,
                id_giao_vien INTEGER,
                FOREIGN KEY (id_giao_vien) REFERENCES giao_vien (id)
            )
        ''')
        # Bảng buổi dạy để tính tiết của giáo viên
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS buoi_day (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_lop INTEGER NOT NULL,
                id_giao_vien INTEGER NOT NULL,
                ngay TEXT NOT NULL,
                FOREIGN KEY (id_lop) REFERENCES lop (id),
                FOREIGN KEY (id_giao_vien) REFERENCES giao_vien (id)
            )
        ''')
        # Bảng học viên với thông tin lớp và học phí
        self.cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS hoc_vien (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ho_ten TEXT NOT NULL,
                ngay_sinh TEXT,
                ngay_nhap_hoc TEXT,
                han_hoc_phi TEXT,
                hoc_phi_goc INT,
                giam_gia REAL DEFAULT 0,
                loai_giam_gia TEXT DEFAULT '%',
                trang_thai_phi TEXT DEFAULT 'Chưa đóng',
                id_lop INTEGER,
                diem_so REAL DEFAULT 0,
                ghi_chu TEXT DEFAULT '',
                FOREIGN KEY (id_lop) REFERENCES lop (id)
            )
        ''')
        # Bảng lịch sử điểm danh
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS diem_danh (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_hoc_vien INTEGER,
                ngay TEXT,
                trang_thai TEXT,
                FOREIGN KEY (id_hoc_vien) REFERENCES hoc_vien (id)
            )
        ''')

        # Di chuyển / thêm cột nếu schema cũ không có
        if self.column_exists('hoc_vien', 'trang_thai_phi') is False:
            self.cursor.execute("ALTER TABLE hoc_vien ADD COLUMN trang_thai_phi TEXT DEFAULT 'Chưa đóng'")
        if self.column_exists('hoc_vien', 'id_lop') is False:
            self.cursor.execute("ALTER TABLE hoc_vien ADD COLUMN id_lop INTEGER")
        self.conn.commit()

    def add_hoc_vien(self, ho_ten, ngay_sinh, han_hoc_phi, hoc_phi_goc, giam_gia, id_lop=None, diem_so=0, ghi_chu=''):
        ngay_nhap = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute('''
            INSERT INTO hoc_vien (ho_ten, ngay_sinh, ngay_nhap_hoc, han_hoc_phi, hoc_phi_goc, giam_gia, loai_giam_gia, id_lop, diem_so, ghi_chu)
            VALUES (?, ?, ?, ?, ?, ?, '%', ?, ?, ?)
        ''', (ho_ten, ngay_sinh, ngay_nhap, han_hoc_phi, hoc_phi_goc, giam_gia, id_lop, diem_so, ghi_chu))
        self.conn.commit()

    def update_hoc_vien(self, id_hv, ho_ten, ngay_sinh, han_hoc_phi, hoc_phi_goc, giam_gia, id_lop, diem_so=0, ghi_chu=''):
        self.cursor.execute('''
            UPDATE hoc_vien SET ho_ten=?, ngay_sinh=?, han_hoc_phi=?, hoc_phi_goc=?, giam_gia=?, id_lop=?, diem_so=?, ghi_chu=? WHERE id=?
        ''', (ho_ten, ngay_sinh, han_hoc_phi, hoc_phi_goc, giam_gia, id_lop, diem_so, ghi_chu, id_hv))
        self.conn.commit()

    def get_all_hoc_vien(self):
        self.cursor.execute('''
            SELECT hv.id, hv.ho_ten, hv.ngay_sinh, hv.han_hoc_phi, hv.hoc_phi_goc,
                   hv.giam_gia, hv.loai_giam_gia, hv.trang_thai_phi, hv.id_lop,
                   COALESCE(lp.ten_lop, 'Chưa phân lớp')
            FROM hoc_vien hv
            LEFT JOIN lop lp ON hv.id_lop = lp.id
        ''')
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()
        
    def get_hoc_vien_theo_phi(self, loc_no_phi=False):
        if loc_no_phi:
            # Lấy những người có trạng thái 'Chưa đóng' HOẶC ngày hạn < hôm nay
            query = '''
                SELECT hv.id, hv.ho_ten, hv.ngay_sinh, hv.han_hoc_phi, hv.hoc_phi_goc,
                       hv.giam_gia, hv.loai_giam_gia, hv.trang_thai_phi, hv.id_lop,
                       COALESCE(lp.ten_lop, 'Chưa phân lớp')
                FROM hoc_vien hv
                LEFT JOIN lop lp ON hv.id_lop = lp.id
                WHERE hv.trang_thai_phi = 'Chưa đóng' OR hv.han_hoc_phi < date('now')
            '''
        else:
            query = '''
                SELECT hv.id, hv.ho_ten, hv.ngay_sinh, hv.han_hoc_phi, hv.hoc_phi_goc,
                       hv.giam_gia, hv.loai_giam_gia, hv.trang_thai_phi, hv.id_lop,
                       COALESCE(lp.ten_lop, 'Chưa phân lớp')
                FROM hoc_vien hv
                LEFT JOIN lop lp ON hv.id_lop = lp.id
            '''
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def cap_nhat_dong_phi(self, id_hv, trang_thai_moi):
        self.cursor.execute("UPDATE hoc_vien SET trang_thai_phi = ? WHERE id = ?", (trang_thai_moi, id_hv))
        self.conn.commit()

    def them_giao_vien(self, ho_ten, luong_mot_tiet, tien_thuong=0):
        self.cursor.execute(
            "INSERT INTO giao_vien (ho_ten, luong_mot_tiet, tien_thuong) VALUES (?, ?, ?)",
            (ho_ten, luong_mot_tiet, tien_thuong)
        )
        self.conn.commit()

    def cap_nhat_giao_vien(self, id_gv, ho_ten, luong_mot_tiet, tien_thuong=0):
        self.cursor.execute(
            "UPDATE giao_vien SET ho_ten=?, luong_mot_tiet=?, tien_thuong=? WHERE id=?",
            (ho_ten, luong_mot_tiet, tien_thuong, id_gv)
        )
        self.conn.commit()

    def xoa_giao_vien(self, id_gv):
        self.cursor.execute("DELETE FROM giao_vien WHERE id=?", (id_gv,))
        self.conn.commit()

    def get_all_giao_vien(self):
        """Trả về: id, ho_ten, luong_mot_tiet, so_lop, tien_thuong"""
        self.cursor.execute("""
            SELECT gv.id,
                   gv.ho_ten,
                   gv.luong_mot_tiet,
                   COALESCE((SELECT COUNT(*) FROM lop WHERE id_giao_vien = gv.id), 0) AS so_lop,
                   COALESCE(gv.tien_thuong, 0) AS tien_thuong
            FROM giao_vien gv
            ORDER BY gv.ho_ten
        """)
        return self.cursor.fetchall()

    def them_lop(self, ten_lop, mo_ta, id_giao_vien=None):
        self.cursor.execute("INSERT INTO lop (ten_lop, mo_ta, id_giao_vien) VALUES (?, ?, ?)",
                            (ten_lop, mo_ta, id_giao_vien))
        self.conn.commit()

    def cap_nhat_lop(self, id_lop, ten_lop, mo_ta, id_giao_vien):
        self.cursor.execute("UPDATE lop SET ten_lop=?, mo_ta=?, id_giao_vien=? WHERE id=?",
                            (ten_lop, mo_ta, id_giao_vien, id_lop))
        self.conn.commit()

    def xoa_lop(self, id_lop):
        self.cursor.execute("UPDATE hoc_vien SET id_lop=NULL WHERE id_lop=?", (id_lop,))
        self.cursor.execute("DELETE FROM buoi_day WHERE id_lop=?", (id_lop,))
        self.cursor.execute("DELETE FROM lop WHERE id=?", (id_lop,))
        self.conn.commit()

    def get_all_lop(self):
        self.cursor.execute('''
            SELECT l.id, l.ten_lop, l.mo_ta, l.id_giao_vien, gv.ho_ten
            FROM lop l
            LEFT JOIN giao_vien gv ON l.id_giao_vien = gv.id
            ORDER BY l.ten_lop
        ''')
        return self.cursor.fetchall()

    def get_all_lop_names(self):
        self.cursor.execute("SELECT id, ten_lop FROM lop ORDER BY ten_lop")
        return self.cursor.fetchall()

    def get_all_teacher_names(self):
        self.cursor.execute("SELECT id, ho_ten FROM giao_vien ORDER BY ho_ten")
        return self.cursor.fetchall()

    def them_buoi_day(self, id_lop, id_giao_vien, ngay):
        self.cursor.execute("INSERT INTO buoi_day (id_lop, id_giao_vien, ngay) VALUES (?, ?, ?)",
                            (id_lop, id_giao_vien, ngay))
        self.conn.commit()

    def get_buoi_day_theo_lop(self, ngay=None):
        if ngay:
            self.cursor.execute('''
                SELECT bd.id, bd.ngay, l.ten_lop, gv.ho_ten
                FROM buoi_day bd
                JOIN lop l ON bd.id_lop = l.id
                JOIN giao_vien gv ON bd.id_giao_vien = gv.id
                WHERE bd.ngay = ?
                ORDER BY bd.ngay DESC
            ''', (ngay,))
        else:
            self.cursor.execute('''
                SELECT bd.id, bd.ngay, l.ten_lop, gv.ho_ten
                FROM buoi_day bd
                JOIN lop l ON bd.id_lop = l.id
                JOIN giao_vien gv ON bd.id_giao_vien = gv.id
                ORDER BY bd.ngay DESC
            ''')
        return self.cursor.fetchall()

    def get_giao_vien_summary(self):
        """Trả về: id, so_lop, so_tiet"""
        self.cursor.execute("""
            SELECT gv.id,
                   COUNT(DISTINCT l.id) AS so_lop,
                   COUNT(b.id) AS so_tiet
            FROM giao_vien gv
            LEFT JOIN lop l ON l.id_giao_vien = gv.id
            LEFT JOIN buoi_day b ON b.id_giao_vien = gv.id
            GROUP BY gv.id
        """)
        return self.cursor.fetchall()

    def diem_danh_va_gia_han(self, id_hv, trang_thai):
        ngay_hien_tai = datetime.now().strftime("%Y-%m-%d")
        # 1. Ghi nhật ký
        self.cursor.execute("INSERT INTO diem_danh (id_hoc_vien, ngay, trang_thai) VALUES (?, ?, ?)", 
                           (id_hv, ngay_hien_tai, trang_thai))
        # 2. Nếu Vắng -> Tự động cộng 1 ngày vào hạn đóng phí
        if trang_thai == "Vắng":
            self.cursor.execute("UPDATE hoc_vien SET han_hoc_phi = date(han_hoc_phi, '+1 day') WHERE id = ?", (id_hv,))
        self.conn.commit()
        
    def get_lich_su_vang(self):
        self.cursor.execute('''
            SELECT dd.ngay, hv.ho_ten FROM diem_danh dd 
            JOIN hoc_vien hv ON dd.id_hoc_vien = hv.id 
            WHERE dd.trang_thai = 'Vắng' ORDER BY dd.ngay DESC
        ''')
        return self.cursor.fetchall()
    
    def get_trang_thai_hom_nay(self, id_hv):
        ngay_hien_tai = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute("SELECT trang_thai FROM diem_danh WHERE id_hoc_vien = ? AND ngay = ?", (id_hv, ngay_hien_tai))
        result = self.cursor.fetchone()
        return result[0] if result else "Chưa có"
    def luu_diem_danh_ngay(self, ngay, danh_sach_id_vang_moi):
        # 1. Lấy danh sách những người ĐÃ VẮNG trước khi cập nhật
        self.cursor.execute("SELECT id_hoc_vien FROM diem_danh WHERE ngay = ? AND trang_thai = 'Vắng'", (ngay,))
        vang_cu = set(row[0] for row in self.cursor.fetchall())
        vang_moi = set(danh_sach_id_vang_moi)

        # 2. Xử lý cộng/trừ ngày học phí dựa trên sự sai lệch
        # Những em bị đánh vắng thêm (Có trong mới, không có trong cũ) -> Cộng 1 ngày hạn phí
        them_moi = vang_moi - vang_cu
        for hv_id in them_moi:
            self.cursor.execute("UPDATE hoc_vien SET han_hoc_phi = date(han_hoc_phi, '+1 day') WHERE id = ?", (hv_id,))

        # Những em được giáo viên gỡ vắng (Có trong cũ, không có trong mới) -> Hoàn tác trừ 1 ngày hạn phí
        bo_di = vang_cu - vang_moi
        for hv_id in bo_di:
            self.cursor.execute("UPDATE hoc_vien SET han_hoc_phi = date(han_hoc_phi, '-1 day') WHERE id = ?", (hv_id,))

        # 3. Làm sạch dữ liệu điểm danh của ngày hôm đó (Xóa hết)
        self.cursor.execute("DELETE FROM diem_danh WHERE ngay = ?", (ngay,))
        
        # 4. Ghi lại danh sách vắng mới
        for hv_id in vang_moi:
            self.cursor.execute("INSERT INTO diem_danh (id_hoc_vien, ngay, trang_thai) VALUES (?, ?, 'Vắng')", (hv_id, ngay))

        self.conn.commit()

    def _ensure_teacher_bonus_column(self):
        try:
            self.cursor.execute("ALTER TABLE giao_vien ADD COLUMN tien_thuong REAL DEFAULT 0")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass

    def get_teacher_session_report(self):
        """Trả về: ho_ten, so_tiet, luong_mot_tiet, tien_thuong"""
        self.cursor.execute("""
            SELECT gv.ho_ten,
                   COUNT(b.id) AS so_tiet,
                   gv.luong_mot_tiet,
                   COALESCE(gv.tien_thuong, 0) AS tien_thuong
            FROM giao_vien gv
            LEFT JOIN buoi_day b ON b.id_giao_vien = gv.id
            GROUP BY gv.id
            ORDER BY gv.ho_ten
        """)
        return self.cursor.fetchall()

# Khởi tạo thử một đối tượng database để tạo file db ngay lập tức
if __name__ == "__main__":
    db = Database()
    print("Đã khởi tạo Database thành công!")
    db.add_hoc_vien("Nguyễn Văn A", "2010-05-15", "2026-04-01")
    db.add_hoc_vien("Trần Thị B", "2011-02-20", "2026-04-05")
    db.close()