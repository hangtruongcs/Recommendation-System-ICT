# Báo cáo validation sau khi áp dụng quy tắc outcome availability

**Trạng thái:** thăm dò, không phải protocol test cuối. Các kết quả cũ vẫn được lưu riêng để đối chiếu. `Payment time` là proxy bảo thủ, chưa được xác minh là thời điểm chính xác mọi trường hóa đơn sẵn có; vì vậy không khẳng định đã loại bỏ toàn bộ leakage.

## 1. Quy tắc được áp dụng

Pilot vẫn dùng `Start Time` để tạo lịch sử tương tác train trước 01/07/2021. Đối với estimator, chỉ xét các phiên train có năng lượng và duration dương, rồi tách hai tập:

1. **Duration:** `End Time` phải nhỏ hơn cutoff, vì duration và năng lượng cuối phiên không thể được giả định đã biết khi phiên chưa kết thúc.
2. **Actual Payment và Transaction Amount:** ngoài điều kiện trên, `Payment time` phải nhỏ hơn cutoff. Điều kiện này là proxy bảo thủ; dữ liệu hiện chưa xác nhận timestamp nào thể hiện chính xác thời điểm các giá trị này sẵn có. Nó cũng được áp dụng cho gross amount để phép kiểm tra cùng chính sách.

Quy tắc outcome không loại một lượt bắt đầu trước cutoff khỏi lịch sử CF chỉ vì outcome đến sau: lịch sử CF biểu thị sự kiện bắt đầu đã ghi nhận, còn outcome vận hành cần điều kiện sẵn có riêng. Các truy vấn validation và candidate catalog không đổi.

| Kiểm tra | Số phiên |
| --- | ---: |
| Cohort vận hành trước điều kiện availability | 251.570 |
| Dùng được cho duration theo end timestamp | 251.543 |
| Dùng được cho cost theo end và payment proxy | 251.358 |
| Loại khỏi duration | 27 |
| Loại khỏi cost | 212 |

Mười hai địa điểm có ít nhất một phiên cost bị loại; địa điểm có số bị loại nhiều nhất là 40 phiên. Tất cả 13 địa điểm vẫn có tối thiểu 5.489 phiên cho cost và 5.498 phiên cho duration. Vì tất cả site đều vượt ngưỡng 30 phiên của pilot, chưa cần fallback; mã dừng với lỗi nếu điều kiện đó không đạt, không tự thay bằng giá trị toàn cục.

## 2. Kết quả validation sau sửa

Các giá trị accuracy và ILD dưới đây là trung bình ba seed 20261120–20261122, BPR-MF tám chiều, trên 4.851 warm validation users. ILD đo khoảng cách giữa cost và duration ước lượng, không đo diversity địa lý hay sở thích.

| Phương pháp | Hit Rate@3 | NDCG@3 | ILD@3 |
| --- | ---: | ---: | ---: |
| Personal frequency | 0,692 | 0,615 | 0,241 |
| BPR-MF | 0,656 | 0,560 | 0,291 |
| Weighted sum | 0,581 | 0,495 | 0,322 |
| Pareto | 0,628 | 0,545 | 0,313 |
| Greedy α = 0,8 | 0,645 | 0,553 | 0,373 |
| Greedy α = 0,5 | 0,617 | 0,534 | 0,480 |

Các chỉ số làm tròn đến ba chữ số gần như giữ nguyên so với pilot cũ, nhưng giá trị chính xác và một số estimator có thay đổi. BPR relevance-only không đổi trong ba seed vì tương tác CF và tập truy vấn không thay đổi. Quan sát này chỉ áp dụng cho quy tắc và bộ dữ liệu đã thử; không thay thế kiểm tra ngữ nghĩa timestamp.

## 3. Đánh giá estimator

Trên 63.374 phiên validation có năng lượng và duration dương, estimator site đạt MAE khoản thực trả **2,21 CNY** so với median toàn cục **3,57 CNY**; duration lần lượt **35,29** và **36,17 phút**. Đây là dự đoán tại địa điểm được chọn, dùng năng lượng thực tế của phiên trong kiểm tra, không phải kiểm chứng phản thực tế cho kịch bản gợi ý 20 kWh. Khoản thực trả có thể chứa giảm giá, và duration vẫn có sai số lớn.

Với seed 20261120, chênh lệch NDCG@3 của Pareto so với BPR là −0,0151; khoảng bootstrap ghép cặp theo user 95% là −0,0198 đến −0,0104. ILD tăng 0,0337; khoảng tương ứng là 0,0304 đến 0,0369. Đây là bất định có điều kiện theo mô hình và validation, không bao gồm bất định do chọn cấu hình hay dataset.

## 4. Tái lập

```sh
for seed in 20261120 20261121 20261122; do
  JIAXING_PILOT_DIM=8 JIAXING_PILOT_SEED=$seed \
    python3 Materials/Code/pilot_jiaxing.py
done
JIAXING_FIGURE_POLICY=availability_proxy \
  python3 Materials/Code/plot_validation_results.py
```

Các JSON và CSV mới có hậu tố `_availability_proxy`. Báo cáo trước đó và các tệp không có hậu tố giữ trạng thái lịch sử. Test vẫn chỉ được kiểm tra số lượng, chưa tính hiệu năng. Trước khi dùng kết quả cho hội nghị cần xác minh ngữ nghĩa timestamp, đánh giá cost/duration theo từng site và nhóm, chốt metric, cohort, cấu hình và protocol rồi mới đánh giá test.
