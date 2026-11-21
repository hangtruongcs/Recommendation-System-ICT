# Hồ sơ báo cáo nhóm — Xu hướng mới trong ICT

**Học phần:** Xu hướng mới trong ICT · CHKHMT15B1 – 706401818301  
**Giảng viên:** Lê Thị Vĩnh Thanh · **Nhóm:** 2

**Tài liệu chính:** [Báo cáo Nhóm 2 – Xu hướng mới trong ICT](Materials/Thesis/Group_2_Emerging_Trends_in_ICT_Report.pdf). Thư mục này tập hợp các tệp trực tiếp liên quan, không phải xác nhận đã đáp ứng mẫu trường.

## Những điểm cần hoàn tất trước khi nộp

- Bổ sung mã số học viên của Nhóm 2; đối chiếu trang bìa, hình thức và yêu cầu nộp với hướng dẫn của giảng viên.
- Xác minh phiên bản Figshare của bản dữ liệu cục bộ, giấy phép và quyền chia sẻ trước khi gửi bộ dữ liệu hoặc hồ sơ cho bên ngoài. `Payment time` là proxy availability chưa xác minh; các phân tích hậu nghiệm trên test được nêu rõ trong luận văn.
- Bản PDF trình bày công thức bằng hình vector: có thể xem/in, nhưng một số công cụ trích xuất không đọc được ký hiệu. Tệp Markdown giữ công thức gốc.

## Cấu trúc

- `Materials/Thesis/`: báo cáo PDF, Markdown và hai hình xuất hiện trong báo cáo.
- `Materials/Code/`: mã thực nghiệm, phân tích, vẽ hình và `pilot_results/` chứa giao thức, kết quả validation, test, cohort và phân tích bổ sung. Thư mục `final_test/` giữ kết quả test và phân tích hậu nghiệm.
- `Materials/Thesis/demo/index.html`: minh họa ứng dụng có thể mở trực tiếp bằng trình duyệt; không phải hệ thống trạm sạc thời gian thực.
- `28182251/Dataset/`: bản dữ liệu cục bộ gồm giao dịch và hai tệp bổ trợ. Mô hình chỉ đọc `Charging_Data.csv`; hai tệp còn lại được giữ để đối chiếu mô tả dữ liệu, không dùng làm đặc trưng mô hình.
- `SHA256SUMS.txt`: mã kiểm tra nội dung từng tệp.

## Chạy lại và kiểm tra

Chạy từ thư mục chứa README này. Môi trường kiểm tra gần nhất: Python 3.11.9, `requirements.txt`; Phiên bản này là môi trường đã kiểm tra, không chứng minh môi trường của mọi lần chạy trước. Cài thư viện trong môi trường ảo phù hợp.

```sh
python3 Materials/Code/audit_outcome_availability.py
JIAXING_PILOT_SEED=20261120 python3 Materials/Code/pilot_jiaxing.py
JIAXING_FIGURE_POLICY=availability_proxy python3 Materials/Code/plot_validation_results.py
```

Thay seed bằng 20261121 và 20261122 để chạy ba cấu hình validation. Các lệnh tạo lại có thể ghi đè kết quả và hình cùng tên: sao chép toàn bộ hồ sơ trước khi chạy. Có thể chạy `final_test_jiaxing.py` theo ba seed để tái tạo kết quả đã báo cáo; đây không phải tập test mới hoặc đánh giá xác nhận độc lập. `analyze_objective_structure.py`, `analyze_test_segments.py` và `analyze_unit_rate_errors.py` là phân tích hậu nghiệm; `explore_validation_robustness.py` là thăm dò validation. Xem `test_protocol.md` để hiểu các điều kiện và giới hạn.

Tính nhất quán số liệu phụ thuộc bản dữ liệu, phiên bản môi trường và các giả thiết trong mã. Việc chạy lại không xác minh ngữ nghĩa nghiệp vụ của timestamp, outcome phản thực tế hay lợi ích thực tế.
