from flask import Flask, request, jsonify
import pandas as pd
import pprint

app = Flask(__name__)

# Đọc dữ liệu từ file Excel
data_file = 'E:/Tương tác người máy/WEB/clothes_data.xlsx'
clothing_df = pd.read_excel(data_file)

# Xóa các ký tự trắng trong tên cột
clothing_df.columns = clothing_df.columns.str.strip()

# Kiểm tra danh sách các cột
print("Danh sách các cột trong DataFrame:")
print(clothing_df.columns.tolist())

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    
    # In log cấu trúc của request
    print("Received request:")
    pprint.pprint(req)

    # Kiểm tra xem request có chứa thông tin không
    if 'queryResult' not in req or 'parameters' not in req['queryResult']:
        return jsonify({'fulfillmentText': 'Không có thông tin yêu cầu từ người dùng.'})

    # Lấy các tham số từ yêu cầu
    query_result = req['queryResult']
    material = query_result['parameters'].get('evatlieu')
    clothing_type = query_result['parameters'].get('eLoai_QuanAo')
    price = query_result['parameters'].get('number')

    # Tạo DataFrame tạm thời để lọc
    results = clothing_df

    # Lọc theo chất liệu nếu có
    if material:
        results = results[results['Chất Liệu'].str.contains(material, case=False, na=False)]

    # Lọc theo loại quần áo nếu có
    if clothing_type:
        results = results[results['Loại quần áo'].str.contains(clothing_type, case=False, na=False)]

    # Lọc theo giá nếu có
    if price:
        results = results[results['Giá'] <= price]

    # Kiểm tra kết quả sau khi lọc
    if not results.empty:
        products = []
        for index, row in results.iterrows():
            products.append({
                'Tên sản phẩm': row['Tên sản phẩm'],
                'Loại quần áo': row['Loại quần áo'],
                'Chất Liệu': row['Chất Liệu'],
                'Giá': f"{row['Giá']} VND",
                'Mô tả': row['Mô tả'],
                'Số lượng': row['Số lượng']
            })
        
        # Định dạng kết quả trả về cho chatbot
        response_text = f"Tìm thấy {len(products)} sản phẩm phù hợp:\n"
        response_text += "\n".join(
            [f"- {p['Tên sản phẩm']} (Loại: {p['Loại quần áo']}, Giá: {p['Giá']}, Số lượng: {p['Số lượng']}, Mô tả: {p['Mô tả']})" for p in products]
        )
        return jsonify({'fulfillmentText': response_text})
    else:
        # Phản hồi nếu không có sản phẩm nào đáp ứng đủ yêu cầu
        return jsonify({'fulfillmentText': 'Không tìm thấy sản phẩm nào phù hợp với tiêu chí tìm kiếm.'})

if __name__ == '__main__':
    app.run(port=5000)

