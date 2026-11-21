# Báo cáo nhóm — Xu hướng mới trong ICT

**Lớp:** CHKHMT15B1 · 706401818301  
**Giảng viên:** Lê Thị Vĩnh Thanh  
**Nhóm 2:** Trương Thị Ngọc Hằng, Ngô Thị Lan Hương, Nguyễn Gia Vũ

Báo cáo khảo sát tái xếp hạng gợi ý địa điểm sạc xe điện bằng Pareto trên dữ liệu lịch sử Jiaxing. Xem [báo cáo PDF](Materials/Thesis/Group_2_Emerging_Trends_in_ICT_Report.pdf) trước; các tệp bên dưới hỗ trợ đối chiếu dữ liệu, phương pháp và kết quả.

## Báo cáo và minh họa

| Tệp | Nội dung |
| --- | --- |
| `Materials/Thesis/Group_2_Emerging_Trends_in_ICT_Report.pdf` | Báo cáo học phần, gồm phương pháp, thực nghiệm, thảo luận và phụ lục. |
| `Materials/Thesis/Thesis_Draft.md` | Nguồn Markdown của báo cáo, chỉ lưu cục bộ và được `.gitignore` loại khỏi Git. |
| `Materials/Thesis/demo/index.html` | Minh họa đề xuất trạm theo các kịch bản và truy vấn ẩn danh; mở trực tiếp bằng trình duyệt. Không phải dịch vụ thời gian thực. |
| `Materials/Thesis/figures/accuracy_diversity_validation_availability_proxy.png` | So sánh độ chính xác và đa dạng trên validation. |
| `Materials/Thesis/figures/estimator_mae_validation_availability_proxy.png` | Sai số MAE của bộ ước lượng chi phí và thời lượng trên validation. |

## Dữ liệu

Các tệp trong `28182251/Dataset/`:

| Tệp | Nội dung và cách dùng |
| --- | --- |
| `Charging_Data.csv` | Dữ liệu giao dịch sạc Jiaxing; đầu vào của các chương trình thực nghiệm. |
| `Time-of-use_Price.csv` | Biểu giá theo thời gian để tham khảo; không được dùng làm đặc trưng mô hình. |
| `Weather_Data.csv` | Dữ liệu thời tiết để tham khảo; không được dùng làm đặc trưng mô hình. |

## Mã thực nghiệm

Các tệp trong `Materials/Code/`:

| Tệp | Vai trò |
| --- | --- |
| `pilot_jiaxing.py` | Huấn luyện và đánh giá thăm dò trên validation, bao gồm các cấu hình cohort. |
| `final_test_jiaxing.py` | Đánh giá trên test theo giao thức đã ghi. |
| `audit_outcome_availability.py` | Kiểm tra thời điểm và tính sẵn có của dữ liệu outcome. |
| `plot_validation_results.py` | Vẽ hai hình validation từ kết quả đã lưu. |
| `pareto_validation_case.py` | Trích một truy vấn validation để giải thích phân tầng Pareto. |
| `explore_validation_robustness.py` | Khảo sát độ nhạy validation khi thay giả thiết thời lượng. |
| `export_demo_queries.py` | Xuất các truy vấn validation ẩn danh để minh họa demo. |
| `analyze_objective_structure.py` | Phân tích hậu nghiệm cấu trúc mục tiêu và các tầng Pareto trên test. |
| `analyze_test_segments.py` | Phân tích hậu nghiệm các nhóm người dùng và chỉ số theo vị trí trong danh sách test. |
| `analyze_unit_rate_errors.py` | Phân tích hậu nghiệm sai số đơn giá và thời lượng trên test. |

## Kết quả validation và giao thức

Các tệp trong `Materials/Code/pilot_results/`. Trong tên kết quả, `dim_8` là số chiều BPR-MF; `seed` là hạt giống ngẫu nhiên. `availability_proxy` chỉ chính sách dùng `Payment time` làm proxy về thời điểm thông tin sẵn có, chưa được xác minh về ngữ nghĩa nghiệp vụ.

| Tệp | Nội dung |
| --- | --- |
| `availability_proxy_validation_report.md` | Diễn giải và hướng dẫn kết quả validation theo chính sách proxy. |
| `results_dim_8_seed_20261120_availability_proxy.json` | Kết quả validation seed 20261120. |
| `results_dim_8_seed_20261121_availability_proxy.json` | Kết quả validation seed 20261121. |
| `results_dim_8_seed_20261122_availability_proxy.json` | Kết quả validation seed 20261122. |
| `results_dim_8_seed_20261120_cohort_positive_energy.json` | Kết quả validation cho cohort năng lượng dương. |
| `results_dim_8_seed_20261120_cohort_positive_energy_nonabnormal.json` | Kết quả validation cho cohort năng lượng dương và không có cờ bất thường. |
| `station_estimates_availability_proxy.csv` | Thống kê và ước lượng theo địa điểm dùng trong validation. |
| `validation_site_errors_availability_proxy.csv` | Sai số ước lượng theo địa điểm trên validation. |
| `validation_robustness_posthoc.json` | Kết quả thăm dò độ nhạy của giả thiết thời lượng trên validation. |
| `pareto_validation_case.json` | Các ứng viên và kết quả phân tầng của truy vấn Pareto minh họa. |
| `demo_validation_cases.json` | Năm truy vấn validation ẩn danh được chọn cho demo; không đại diện toàn bộ người dùng. |
| `outcome_availability_audit.json` | Kết quả kiểm tra timestamp và tính sẵn có của outcome. |
| `test_protocol.md` | Giao thức test được cố định sau khi xem validation; cần đọc trước khi diễn giải test. |

## Kết quả test

Các tệp trong `Materials/Code/pilot_results/final_test/`:

| Tệp | Nội dung |
| --- | --- |
| `results_dim_8_seed_20261120_availability_proxy.json` | Kết quả test seed 20261120. |
| `results_dim_8_seed_20261121_availability_proxy.json` | Kết quả test seed 20261121. |
| `results_dim_8_seed_20261122_availability_proxy.json` | Kết quả test seed 20261122. |
| `station_estimates_availability_proxy.csv` | Thống kê và ước lượng theo địa điểm cho test. |
| `test_site_errors_availability_proxy.csv` | Sai số ước lượng theo địa điểm trên test. |
| `objective_structure_posthoc.json` | Phân tích hậu nghiệm tương quan mục tiêu và cấu trúc Pareto. |
| `segments_and_list_metrics_posthoc.json` | Kết quả hậu nghiệm theo nhóm người dùng và vị trí trong danh sách. |
| `unit_rate_errors_posthoc.json` | Kết quả hậu nghiệm về sai số đơn giá và thời lượng. |

Các bảng trung gian theo quý và theo từng cohort đã được lược khỏi hồ sơ; mã có thể tạo lại khi thực nghiệm được chạy lại.

## Tệp hỗ trợ

| Tệp | Nội dung |
| --- | --- |
| `requirements.txt` | Các thư viện Python cần cài. |
| `.gitignore` | Quy tắc không đưa bản thảo Markdown cục bộ lên Git. |
| `SHA256SUMS.txt` | Mã SHA-256 để kiểm tra tính toàn vẹn các tệp trong hồ sơ cục bộ. |
| `README.md` | Hướng dẫn đọc và chạy hồ sơ này. |

## Chạy lại

Chạy từ thư mục chứa README. Môi trường được kiểm tra gần nhất là Python 3.11.9. Tạo môi trường ảo và cài thư viện:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Sau đó chạy kiểm tra availability, validation và vẽ hình:

```sh
python3 Materials/Code/audit_outcome_availability.py
JIAXING_PILOT_SEED=20261120 python3 Materials/Code/pilot_jiaxing.py
JIAXING_PILOT_SEED=20261121 python3 Materials/Code/pilot_jiaxing.py
JIAXING_PILOT_SEED=20261122 python3 Materials/Code/pilot_jiaxing.py
JIAXING_FIGURE_POLICY=availability_proxy python3 Materials/Code/plot_validation_results.py
```

Để tái tạo test đã báo cáo, chạy `final_test_jiaxing.py` cho từng seed sau khi đọc `test_protocol.md`. Chạy lại có thể ghi đè kết quả và hình; nên sao chép hồ sơ trước khi chạy. Kết quả phụ thuộc dữ liệu, môi trường và giả thiết; test chạy lại không phải đánh giá xác nhận độc lập.

Trước khi nộp, cần bổ sung mã số học viên, đối chiếu yêu cầu của giảng viên và xác minh phiên bản, giấy phép cùng quyền chia sẻ dữ liệu. PDF hiển thị công thức bằng hình vector nên một số công cụ có thể không trích xuất được ký hiệu.
