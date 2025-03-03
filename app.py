from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100),  nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)  
    products = db.relationship('Product', backref='vendor', lazy=True)
    orders = db.relationship('Order', backref='customer', lazy=True)
    
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    return_eligibility = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(50), default='Pending')

    def check_return_eligibility(self):
        return (datetime.utcnow() - self.order_date) <= timedelta(days=2)
    
class DeliveryDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    receiver_name = db.Column(db.String(100), nullable=False)
    mobile_number = db.Column(db.String(15), nullable=False)
    address = db.Column(db.Text, nullable=False)
    landmark = db.Column(db.String(100))

    def __init__(self, receiver_name, mobile_number, address, landmark):
        self.receiver_name = receiver_name
        self.mobile_number = mobile_number
        self.address = address
        self.landmark = landmark







#  first route for home page
@app.route('/')
def home():
    products = Product.query.all()
    return render_template('index.html', products=products)

# second  route for about page
@app.route('/about')
def about():
    return render_template("about.html")


# third route for login and register page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']

        # Check if the user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash(f'You are already registered as a {existing_user.role}. Please log in.', 'warning')
            return redirect(url_for('login'))

        # Create a new user
        user = User(username=username, email=email, password=password, role=role)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# fourth route for the logout page
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


# fivith route for the vender to add product
@app.route('/vendor/add_product', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session or session['role'] != 'vendor':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        image = request.form['image']
        vendor_id = session['user_id']  # Fetch vendor ID from session

        # Save product to database
        new_product = Product(name=name, description=description, price=price, image=image, vendor_id=vendor_id)
        db.session.add(new_product)
        db.session.commit()

        flash('Product added successfully!', 'success')

        # Redirect to the cart where the product should be visible
        return redirect(url_for('cart'))

    # Fetch all products added by the vendor
    products = Product.query.filter_by(vendor_id=session['user_id']).all()
    return render_template('add_product.html', products=products)


# sixith route for the cart page 
@app.route('/cart')
def cart():
    if 'user_id' not in session:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    # Retrieve all products added to the cart
    products = Product.query.order_by(Product.id.desc()).all()

    # Calculate total price and total quantity
    total_amount = sum(product.price for product in products)
    total_quantity = len(products)

    return render_template('cart.html', products=products, total_amount=total_amount, total_quantity=total_quantity)

# seventh route for the remove the product form cart page
@app.route('/cart/remove/<int:product_id>', methods=['POST'])
def remove_product(product_id):
    if 'user_id' not in session:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    product = Product.query.get(product_id)

    if product:
        db.session.delete(product)
        db.session.commit()
        flash('Product removed successfully!', 'success')
    else:
        flash('Product not found!', 'danger')

    return redirect(url_for('cart'))

# eigth route for the address
@app.route('/cart/address', methods=['GET', 'POST'])
def enter_address():
    if 'user_id' not in session:
        flash('Please log in to continue.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        receiver_name = request.form.get('receiver_name')
        mobile_number = request.form.get('mobile_number')
        address = request.form.get('address')
        landmark = request.form.get('landmark', '')

        # Validate form inputs
        if not receiver_name or not mobile_number or not address:
            flash('All fields except landmark are required!', 'danger')
            return redirect(url_for('enter_address'))

        # Store in session (optional) for later use
        session['address'] = address

        # Save to database
        new_entry = DeliveryDetails(
            receiver_name=receiver_name,
            mobile_number=mobile_number,
            address=address,
            landmark=landmark
        )
        db.session.add(new_entry)
        db.session.commit()

        flash('Address saved successfully!', 'success')
        return redirect(url_for('select_payment_method'))  # Next step: Payment

    return render_template('address.html')

@app.route('/cart/payment_method', methods=['GET', 'POST'])
def select_payment_method():
    if 'user_id' not in session or 'address' not in session:
        flash('Please complete address entry first.', 'warning')
        return redirect(url_for('enter_address'))

    if request.method == 'POST':
        payment_method = request.form.get('payment_method')

        if not payment_method:
            flash('Please select a payment method!', 'danger')
            return redirect(url_for('select_payment_method'))

        session['payment_method'] = payment_method
        return redirect(url_for('place_order'))

    return render_template('payment_method.html')

@app.route('/cart/place_order', methods=['GET', 'POST'])
def place_order():
    if 'user_id' not in session or 'address' not in session or 'payment_method' not in session:
        flash('Please complete all steps.', 'warning')
        return redirect(url_for('enter_address'))

    user = User.query.get(session['user_id'])
    cart_products = Product.query.all()  # Fetch products in cart

    if not cart_products:
        flash('Your cart is empty!', 'danger')
        return redirect(url_for('cart'))

    total_amount = sum(product.price for product in cart_products)
    address = session['address']
    payment_method = session['payment_method']

    if payment_method == 'UPI':
        upi_app = request.form.get('upi_app')
        flash(f'Redirecting to {upi_app} for payment of ₹{total_amount}', 'info')
        return redirect(url_for('upi_payment', upi_app=upi_app, amount=total_amount))

    elif payment_method == 'Card':
        card_number = request.form.get('card_number')
        expiry = request.form.get('expiry')
        cvv = request.form.get('cvv')

        if not card_number or not expiry or not cvv:
            flash('Enter complete card details!', 'danger')
            return redirect(url_for('select_payment_method'))

        flash('Processing card payment...', 'info')
        return redirect(url_for('card_payment', amount=total_amount))

    elif payment_method == 'COD':
        new_order = Order(user_id=user.id, address=address, total_amount=total_amount, payment_method='COD')
        db.session.add(new_order)
        db.session.commit()

        # Clear session data after successful order
        session.pop('address', None)
        session.pop('payment_method', None)

        flash('Order placed successfully! Pay on delivery.', 'success')
        return redirect(url_for('cart'))

    return render_template('place_order.html', user=user, total_amount=total_amount)

@app.route('/payment_success')
def payment_success():
    return render_template('success.html', parent_template='parent.html')

@app.route('/load_more_products')
def load_more_products():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of products to load per request
    products = Product.query.paginate(page=page, per_page=per_page, error_out=False)

    product_list = [{
        "name": p.name,
        "description": p.description,
        "price": p.price,
        "image": p.image
    } for p in products.items]

    return jsonify({"products": product_list})


@app.route('/upi_payment/<upi_app>/<float:amount>')
def upi_payment(upi_app, amount):
    flash(f'Processing {upi_app} payment for ₹{amount}', 'info')
    return redirect(url_for('cart'))


@app.route('/card_payment/<float:amount>')
def card_payment(amount):
    flash(f'Card payment of ₹{amount} successful!', 'success')
    return redirect(url_for('cart'))


# contact 
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        flash('Your message has been sent!', 'success')
        return redirect(url_for('home'))
    return render_template('contact.html')



# Run the application
if __name__ == '__main__':
    app.run(debug=True)





