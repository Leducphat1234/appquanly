from database import Database

db = Database()
# Thêm vài dòng mẫu
db.add_hoc_vien("Nguyễn Văn A", "2010-01-01", "2026-05-01")
db.add_hoc_vien("Lê Thị B", "2011-05-20", "2026-06-15")
db.close()
print("Đã nạp dữ liệu mẫu thành công!")
