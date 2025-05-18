from flask import Flask, request, jsonify  # type: ignore
from flask_cors import CORS
from functools import wraps
import mysql.connector  # type: ignore

app = Flask(__name__)
CORS(app)

# Conexión a la base de datos
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="tiendaautos"
)

cursor = db.cursor(dictionary=True)

@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    cursor.execute("SELECT * FROM users WHERE id = %s", (id,))
    user = cursor.fetchone()
    if not user:
        return jsonify({"message": "User not found"}), 404
    cursor.execute("DELETE FROM users WHERE id = %s", (id,))
    db.commit()
    return jsonify({"message": f"User with ID {id} deleted"}), 200

@app.route('/users', methods=['POST'])
def add_user():
    data = request.json
    query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
    cursor.execute(query, (data['username'], data['email'], data['password']))
    db.commit()
    return jsonify({"message": "User added successfully!"}), 201

@app.route('/users', methods=['GET'])
def get_users():
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    return jsonify(users), 200

@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    cursor.execute("SELECT * FROM users WHERE id = %s", (id,))
    user = cursor.fetchone()
    if user:
        return jsonify(user), 200
    return jsonify({"message": "User not found"}), 404

@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    data = request.json

    # Verificar que el usuario existe
    cursor.execute("SELECT * FROM users WHERE id = %s", (id,))
    user = cursor.fetchone()
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Preparar la consulta de actualización
    query = "UPDATE users SET username = %s, email = %s"
    params = [data['username'], data['email']]

    # Si se incluye la contraseña, actualizarla también
    if 'password' in data:
        query += ", password = %s"
        params.append(data['password'])

    query += " WHERE id = %s"
    params.append(id)

    cursor.execute(query, tuple(params))
    db.commit()

    return jsonify({"message": "User updated successfully!"}), 200

@app.route('/cars', methods=['POST'])
def add_car():
    data = request.json
    query = """
    INSERT INTO cars (make, model, year, price, description, image_url)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (
        data['make'],
        data['model'],
        data['year'],
        data['price'],
        data['description'],
        data['image_url']
    ))
    db.commit()
    return jsonify({"message": "Car added successfully!"}), 201

@app.route('/cars/<int:id>', methods=['PUT'])
def update_car(id):
    data = request.json
    cursor.execute("SELECT * FROM cars WHERE id = %s", (id,))
    car = cursor.fetchone()
    if not car:
        return jsonify({"message": "Car not found"}), 404

    query = """
        UPDATE cars
        SET make = %s, model = %s, year = %s, price = %s, description = %s, image_url = %s
        WHERE id = %s
    """
    cursor.execute(query, (
        data['make'],
        data['model'],
        data['year'],
        data['price'],
        data['description'],
        data['image_url'],
        id
    ))
    db.commit()
    return jsonify({"message": "Car updated successfully!"}), 200


@app.route('/cars', methods=['GET'])
def get_cars():
    cursor.execute("SELECT * FROM cars")
    cars = cursor.fetchall()
    return jsonify(cars), 200

@app.route('/cars/<int:id>', methods=['GET'])
def get_car(id):
    cursor.execute("SELECT * FROM cars WHERE id = %s", (id,))
    car = cursor.fetchone()
    if car:
        return jsonify(car), 200
    return jsonify({"message": "Car not found"}), 404

@app.route('/cars/<int:id>', methods=['DELETE'])
def delete_car(id):
    cursor.execute("SELECT * FROM cars WHERE id = %s", (id,))
    car = cursor.fetchone()
    if car:
        cursor.execute("DELETE FROM cars WHERE id = %s", (id,))
        db.commit()
        return jsonify({"message": f"Car with id {id} has been deleted successfully!"}), 200
    return jsonify({"message": "Car not found"}), 404

@app.route('/orders', methods=['POST'])
def add_order():
    data = request.json
    query = "INSERT INTO orders (user_id, car_id, status) VALUES (%s, %s, %s)"
    cursor.execute(query, (data['user_id'], data['car_id'], data['status']))
    db.commit()
    return jsonify({"message": "Order created successfully!"}), 201

@app.route('/orders', methods=['GET'])
def get_orders():
    query = """
    SELECT orders.id AS order_id, cars.* 
    FROM orders
    JOIN cars ON orders.car_id = cars.id
    WHERE orders.user_id = %s
    """
    user_id = request.args.get('user_id')
    cursor.execute(query, (user_id,))
    orders = cursor.fetchall()
    return jsonify(orders), 200

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    query = "SELECT id, username, email, is_admin FROM users WHERE email=%s AND password=%s"
    cursor.execute(query, (data['email'], data['password']))
    user = cursor.fetchone()
    if not user:
        return jsonify({"message": "Credenciales inválidas"}), 401

    # Devuelve también is_admin
    return jsonify({
        "id": user['id'],
        "username": user['username'],
        "email": user['email'],
        "is_admin": bool(user['is_admin'])
    }), 200



@app.route('/orders/<int:id>', methods=['GET'])
def get_order(id):
    cursor.execute("SELECT * FROM orders WHERE id = %s", (id,))
    order = cursor.fetchone()
    if order:
        return jsonify(order), 200
    return jsonify({"message": "Order not found"}), 404

def admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        user_id = request.headers.get("X-User-Id")
        cursor.execute("SELECT is_admin FROM users WHERE id=%s", (user_id,))
        u = cursor.fetchone()
        if not u or not u['is_admin']:
            return jsonify({"message": "Forbidden"}), 403
        return f(*args, **kwargs)
    return wrapped

@app.route('/orders/all', methods=['GET'])
def get_all_orders():
    cursor.execute("""
        SELECT orders.id AS order_id, users.username, cars.make, cars.model, orders.status
        FROM orders
        JOIN users ON orders.user_id = users.id
        JOIN cars ON orders.car_id = cars.id
    """)
    orders = cursor.fetchall()
    return jsonify(orders), 200

@app.route('/reviews', methods=['POST'])
def add_review():
    data = request.json
    query = """
    INSERT INTO reviews (user_id, car_id, rating, comment)
    VALUES (%s, %s, %s, %s)
    """
    cursor.execute(query, (data['user_id'], data['car_id'], data['rating'], data['comment']))
    db.commit()
    return jsonify({"message": "Review added successfully!"}), 201

@app.route('/reviews', methods=['GET'])
def get_reviews():
    cursor.execute("SELECT * FROM reviews")
    reviews = cursor.fetchall()
    return jsonify(reviews), 200

@app.route('/reviews/car/<int:car_id>', methods=['GET'])
def get_reviews_by_car(car_id):
    cursor.execute("SELECT * FROM reviews WHERE car_id = %s", (car_id,))
    reviews = cursor.fetchall()
    return jsonify(reviews), 200

@app.route('/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    # Verificar si la orden existe
    cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
    order = cursor.fetchone()
    
    if not order:
        return jsonify({"message": "Order not found"}), 404

    # Eliminar la orden
    cursor.execute("DELETE FROM orders WHERE id = %s", (order_id,))
    db.commit()

    return jsonify({"message": f"Order with ID {order_id} has been successfully deleted!"}), 200

@app.route('/orders/user/<int:user_id>', methods=['DELETE'])
def delete_orders_by_user(user_id):
    # Verificar si hay órdenes asociadas al usuario
    cursor.execute("SELECT * FROM orders WHERE user_id = %s", (user_id,))
    orders = cursor.fetchall()

    if not orders:
        return jsonify({"message": "No orders found for this user"}), 404

    # Eliminar todas las órdenes del usuario
    cursor.execute("DELETE FROM orders WHERE user_id = %s", (user_id,))
    db.commit()

    return jsonify({"message": f"All orders for user ID {user_id} have been successfully deleted!"}), 200





if __name__ == '__main__':
    app.run(debug=True)
