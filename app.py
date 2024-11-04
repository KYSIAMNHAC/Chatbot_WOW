from flask import Flask, render_template, request, redirect, url_for
from flask import Flask, request, jsonify
import pandas as pd
import pprint
app = Flask(__name__)

# Dữ liệu sản phẩm mẫu
products = [
    {"id": 1, "name": "Sản phẩm 1", "price": 100000, "description": "Mô tả sản phẩm 1", "image": "images/ANH(1).jpg"},
    {"id": 2, "name": "Sản phẩm 2", "price": 200000, "description": "Mô tả sản phẩm 2", "image": "images/ANH(2).jpg"},
    {"id": 3, "name": "Sản phẩm 3", "price": 300000, "description": "Mô tả sản phẩm 3", "image": "images/ANH(3).jpg"},
    {"id": 4, "name": "Sản phẩm 4", "price": 400000, "description": "Mô tả sản phẩm 4", "image": "images/ANH(4).jpg"},
    {"id": 5, "name": "Sản phẩm 5", "price": 500000, "description": "Mô tả sản phẩm 5", "image": "images/ANH(5).jpg"},
]

# Giỏ hàng lưu trữ sản phẩm mà người dùng thêm vào
cart = []

@app.route('/')
def index():
    return render_template('index.html', products=products)

@app.route('/product/<int:product_id>')
def product(product_id):
    product = next((p for p in products if p["id"] == product_id), None)
    return render_template('product.html', product=product)

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    product = next((p for p in products if p["id"] == product_id), None)
    if product:
        cart.append(product)
    return redirect(url_for('cart_page'))  # Sửa tên endpoint ở đây

@app.route('/cart')
def cart_page():
    return render_template('cart.html', cart=cart)
@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    global cart
    cart = [item for item in cart if item['id'] != product_id]  # Loại bỏ sản phẩm khỏi giỏ hàng
    return redirect(url_for('cart_page'))

# Đọc dữ liệu từ file Excel
data_file = 'clothes_data.xlsx'
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
    app.run(debug=True)
