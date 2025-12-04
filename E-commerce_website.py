# app.py - single-file modern-minimal ecommerce demo (templates & static written automatically)
# Save this file into your ecommerce folder and run with Thonny (F5).
# Payment: simulated by default. Optional Stripe integration if you set STRIPE_SECRET_KEY and STRIPE_PUBLISHABLE_KEY env vars and install stripe package.

import os
import shutil
from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import pathlib

# Optional Stripe support (install 'stripe' package to enable)
try:
    import stripe
    STRIPE_AVAILABLE = True
except Exception:
    STRIPE_AVAILABLE = False

APP_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(APP_DIR, "templates")
STATIC_DIR = os.path.join(APP_DIR, "static")
IMG_DIR = os.path.join(STATIC_DIR, "img")
CSS_DIR = os.path.join(STATIC_DIR, "css")

# Create folders if missing
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(CSS_DIR, exist_ok=True)

# If you uploaded an image and it's present at this path, copy it to static/img
UPLOADED_IMAGE_PATH = "/mnt/data/9efd1b37-1f7e-4ee4-bc84-d93ee71e1cb8.png"
if os.path.exists(UPLOADED_IMAGE_PATH):
    try:
        shutil.copy(UPLOADED_IMAGE_PATH, os.path.join(IMG_DIR, "product_demo.jpg"))
    except Exception as e:
        print("Could not copy uploaded demo image:", e)

# Write a simple CSS for modern minimal style
CSS_CONTENT = """
/* static/css/style.css - modern minimal styles */
body { font-family: "Segoe UI", Roboto, Arial, sans-serif; background:#f5f6f8; color:#222; }
.navbar { background: #ffffff; border-bottom: 1px solid #e7e7e7; box-shadow: 0 1px 0 rgba(0,0,0,0.02);}
.container { max-width: 1200px; margin: 20px auto; padding: 0 16px; }
.header-row { display:flex; align-items:center; gap:16px; padding:12px 0; }
.logo { font-weight:700; font-size:20px; color:#222; }
.search-bar { flex:1; display:flex; }
.search-bar input { flex:1; padding:10px 14px; border-radius:6px 0 0 6px; border:1px solid #ddd; }
.search-bar button { padding:10px 14px; border-radius:0 6px 6px 0; border:1px solid #ddd; background:#222; color:white; }
.header-actions { display:flex; gap:8px; }
.btn-light { padding:8px 12px; border-radius:6px; border:1px solid #ddd; background:white; text-decoration:none; color:#222; }
.grid { display:grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap:16px; margin-top:18px; }
.card { background:white; border-radius:8px; padding:12px; box-shadow: 0 2px 6px rgba(0,0,0,0.03); display:flex; flex-direction:column; gap:8px; }
.card img { width:100%; height:180px; object-fit:cover; border-radius:6px; }
.card .title { font-size:15px; font-weight:600; color:#111; min-height:40px; }
.card .price { font-size:16px; color:#111; font-weight:700; }
.card .meta { color:#666; font-size:13px; }
.card .actions { margin-top:auto; display:flex; gap:8px; }
.btn-primary { background:#ff6f00; color:white; padding:8px 10px; border-radius:6px; text-decoration:none; }
.small { font-size:13px; }
.alert { padding:10px 12px; background:#e8f4ff; border:1px solid #bfe0ff; border-radius:6px; color:#036; }
.form-row { display:flex; gap:8px; margin-bottom:8px; }
.form-row input, .form-row select { padding:8px; border:1px solid #ddd; border-radius:6px; flex:1; }
.footer { text-align:center; color:#999; margin:28px 0; }
.cart-list { display:flex; flex-direction:column; gap:10px; }
.cart-item { display:flex; gap:12px; background:white; padding:10px; border-radius:8px; align-items:center; }
.cart-item img { width:90px; height:70px; object-fit:cover; border-radius:6px; }
@media (max-width:600px) {
  .header-row { flex-direction:column; align-items:stretch; gap:8px; }
}
"""
with open(os.path.join(CSS_DIR, "style.css"), "w", encoding="utf-8") as f:
    f.write(CSS_CONTENT)

# Write templates
BASE_HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>My Mini Shop</title>
  <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
  <div class="container">
    <div class="header-row">
      <div style="display:flex; align-items:center; gap:12px;">
        <div class="logo"><a href="/" style="text-decoration:none; color:inherit">MiniShop</a></div>
        <div class="small" style="color:#666">Modern Minimal Store</div>
      </div>

      <form class="search-bar" method="get" action="/search">
        <input name="q" placeholder="Search for products, e.g. shoes, saree, makeup">
        <button type="submit">Search</button>
      </form>

      <div class="header-actions">
        {% if session.get('user_id') %}
          <a class="btn-light" href="/cart">Cart ({{ cart_count }})</a>
          <a class="btn-light" href="/orders">Orders</a>
          <a class="btn-light" href="/logout">Logout</a>
        {% else %}
          <a class="btn-light" href="/login">Login</a>
          <a class="btn-light" href="/register">Register</a>
        {% endif %}
        <a class="btn-light" href="/admin">Admin</a>
      </div>
    </div>

    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <div style="margin-top:12px;">
          {% for m in messages %}
            <div class="alert">{{ m }}</div>
          {% endfor %}
        </div>
      {% endif %}
    {% endwith %}

    {% block content %}{% endblock %}

    <div class="footer">Built with ❤️ — Demo store · Not for production</div>
  </div>
</body>
</html>
"""
with open(os.path.join(TEMPLATES_DIR, "base.html"), "w", encoding="utf-8") as f:
    f.write(BASE_HTML)

INDEX_HTML = """{% extends "base.html" %}
{% block content %}
  <h2>Featured Products</h2>
  <div class="grid">
    {% for p in products %}
      <div class="card">
        <img src="{{ p.image_url }}" alt="{{ p.name }}">
        <div class="title">{{ p.name }}</div>
        <div class="meta small">{{ p.description or '' }}</div>
        <div class="price">₹{{ "%.2f"|format(p.price) }}</div>
        <div class="actions">
          <a class="btn-primary" href="/add_to_cart/{{ p.id }}">Add to Cart</a>
          <a class="btn-light" href="/product/{{ p.id }}">View</a>
        </div>
      </div>
    {% endfor %}
  </div>
{% endblock %}
"""
with open(os.path.join(TEMPLATES_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(INDEX_HTML)

SEARCH_HTML = """{% extends "base.html" %}
{% block content %}
  <h2>Search results for "{{ query }}"</h2>
  <div class="grid">
    {% if results %}
      {% for p in results %}
        <div class="card">
          <img src="{{ p.image_url }}" alt="{{ p.name }}">
          <div class="title">{{ p.name }}</div>
          <div class="price">₹{{ "%.2f"|format(p.price) }}</div>
          <div class="actions">
            <a class="btn-primary" href="/add_to_cart/{{ p.id }}">Add to Cart</a>
            <a class="btn-light" href="/product/{{ p.id }}">View</a>
          </div>
        </div>
      {% endfor %}
    {% else %}
      <div class="alert">No products found.</div>
    {% endif %}
  </div>
{% endblock %}
"""
with open(os.path.join(TEMPLATES_DIR, "search.html"), "w", encoding="utf-8") as f:
    f.write(SEARCH_HTML)

PRODUCT_HTML = """{% extends "base.html" %}
{% block content %}
  <div style="display:flex; gap:20px; margin-top:18px">
    <div style="flex:1; max-width:420px">
      <img src="{{ product.image_url }}" style="width:100%; border-radius:8px;">
    </div>
    <div style="flex:2">
      <h2>{{ product.name }}</h2>
      <div class="price">₹{{ "%.2f"|format(product.price) }}</div>
      <p class="meta">{{ product.description or '' }}</p>
      <div style="margin-top:14px;">
        <a class="btn-primary" href="/add_to_cart/{{ product.id }}">Add to Cart</a>
        <a class="btn-light" href="/">Continue shopping</a>
      </div>
    </div>
  </div>
{% endblock %}
"""
with open(os.path.join(TEMPLATES_DIR, "product.html"), "w", encoding="utf-8") as f:
    f.write(PRODUCT_HTML)

ADMIN_HTML = """{% extends "base.html" %}
{% block content %}
  <h2>Admin - Add Product</h2>
  <form method="POST" enctype="multipart/form-data" style="max-width:680px; margin-top:12px;">
    <div class="form-row">
      <input type="text" name="name" placeholder="Product name" required>
      <input type="number" step="0.01" name="price" placeholder="Price (₹)" required>
    </div>
    <div style="margin-bottom:8px;">
      <input type="text" name="description" placeholder="Short description (optional)" style="width:100%; padding:8px; border-radius:6px; border:1px solid #ddd;">
    </div>
    <div style="margin-bottom:8px;">
      <input type="file" name="image" required>
    </div>
    <div>
      <button class="btn-primary" type="submit">Add Product</button>
    </div>
  </form>

  <h3 style="margin-top:24px;">Existing products</h3>
  <div style="display:grid; gap:10px;">
    {% for p in products %}
      <div style="display:flex; gap:10px; align-items:center; background:white; padding:10px; border-radius:8px;">
        <img src="{{ p.image_url }}" style="width:80px; height:60px; object-fit:cover; border-radius:6px;">
        <div style="flex:1;">
          <div style="font-weight:600">{{ p.name }}</div>
          <div class="small">₹{{ "%.2f"|format(p.price) }}</div>
        </div>
        <div>
          <a class="btn-light" href="/delete_product/{{ p.id }}" onclick="return confirm('Delete product?')">Delete</a>
        </div>
      </div>
    {% endfor %}
  </div>
{% endblock %}
"""
with open(os.path.join(TEMPLATES_DIR, "admin.html"), "w", encoding="utf-8") as f:
    f.write(ADMIN_HTML)

LOGIN_HTML = """{% extends "base.html" %}
{% block content %}
  <h2>Login</h2>
  <form method="POST" style="max-width:420px;">
    <div class="form-row">
      <input type="text" name="email" placeholder="Email" required>
    </div>
    <div class="form-row">
      <input type="password" name="password" placeholder="Password" required>
    </div>
    <div>
      <button class="btn-primary" type="submit">Login</button>
      <a class="btn-light" href="/register">Register</a>
    </div>
  </form>
{% endblock %}
"""
with open(os.path.join(TEMPLATES_DIR, "login.html"), "w", encoding="utf-8") as f:
    f.write(LOGIN_HTML)

REGISTER_HTML = """{% extends "base.html" %}
{% block content %}
  <h2>Register</h2>
  <form method="POST" style="max-width:420px;">
    <div class="form-row">
      <input type="text" name="name" placeholder="Your name" required>
      <input type="text" name="email" placeholder="Email" required>
    </div>
    <div class="form-row">
      <input type="password" name="password" placeholder="Password" required>
      <input type="password" name="password2" placeholder="Confirm password" required>
    </div>
    <div>
      <button class="btn-primary" type="submit">Create account</button>
    </div>
  </form>
{% endblock %}
"""
with open(os.path.join(TEMPLATES_DIR, "register.html"), "w", encoding="utf-8") as f:
    f.write(REGISTER_HTML)

CART_HTML = """{% extends "base.html" %}
{% block content %}
  <h2>Your Cart</h2>
  {% if items %}
    <div class="cart-list">
      {% for it in items %}
        <div class="cart-item">
          <img src="{{ it.product.image_url }}">
          <div style="flex:1;">
            <div style="font-weight:600">{{ it.product.name }}</div>
            <div class="small">₹{{ "%.2f"|format(it.product.price) }} × {{ it.quantity }}</div>
          </div>
          <div style="text-align:right;">
            <div class="price">₹{{ "%.2f"|format(it.product.price * it.quantity) }}</div>
            <a class="btn-light" href="/remove_from_cart/{{ it.product.id }}">Remove</a>
          </div>
        </div>
      {% endfor %}
    </div>
    <div style="margin-top:14px;">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <div class="small">Total</div>
        <div class="price">₹{{ "%.2f"|format(total) }}</div>
      </div>
      <div style="margin-top:12px;">
        <a class="btn-primary" href="/checkout">Proceed to Checkout</a>
      </div>
    </div>
  {% else %}
    <div class="alert">Your cart is empty.</div>
  {% endif %}
{% endblock %}
"""
with open(os.path.join(TEMPLATES_DIR, "cart.html"), "w", encoding="utf-8") as f:
    f.write(CART_HTML)

CHECKOUT_HTML = """{% extends "base.html" %}
{% block content %}
  <h2>Checkout</h2>

  {% if simulate %}
    <div class="alert">Stripe keys not configured or stripe package missing. Using <strong>simulated</strong> payment flow.</div>
  {% endif %}

  <div style="max-width:720px;">
    <form method="POST">
      <div style="margin-bottom:8px;">
        <input name="address" placeholder="Shipping address" style="width:100%; padding:10px; border-radius:6px; border:1px solid #ddd;" required>
      </div>
      <div style="margin-bottom:8px;">
        <input name="phone" placeholder="Phone number" style="width:100%; padding:10px; border-radius:6px; border:1px solid #ddd;" required>
      </div>
      <div style="margin-bottom:12px;">
        <button class="btn-primary" type="submit">Pay ₹{{ "%.2f"|format(total) }}</button>
      </div>
    </form>
  </div>
{% endblock %}
"""
with open(os.path.join(TEMPLATES_DIR, "checkout.html"), "w", encoding="utf-8") as f:
    f.write(CHECKOUT_HTML)

ORDERS_HTML = """{% extends "base.html" %}
{% block content %}
  <h2>Your Orders</h2>
  {% if orders %}
    <div style="display:flex; flex-direction:column; gap:10px;">
      {% for o in orders %}
        <div style="background:white; padding:10px; border-radius:8px;">
          <div style="display:flex; justify-content:space-between;">
            <div>Order #{{ o.id }} · {{ o.created_at.strftime('%Y-%m-%d %H:%M') }}</div>
            <div class="small">Status: {{ o.status }}</div>
          </div>
          <div style="margin-top:6px;">
            {% for item in o.items %}
              <div style="display:flex; gap:10px; margin-top:6px; align-items:center;">
                <img src="{{ item.product.image_url }}" style="width:70px; height:60px; object-fit:cover; border-radius:6px;">
                <div>
                  <div style="font-weight:600;">{{ item.product.name }}</div>
                  <div class="small">Qty: {{ item.quantity }} · ₹{{ '%.2f'|format(item.product.price * item.quantity) }}</div>
                </div>
              </div>
            {% endfor %}
          </div>
        </div>
      {% endfor %}
    </div>
  {% else %}
    <div class="alert">You have no orders yet.</div>
  {% endif %}
{% endblock %}
"""
with open(os.path.join(TEMPLATES_DIR, "orders.html"), "w", encoding="utf-8") as f:
    f.write(ORDERS_HTML)

# Flask app setup
app = Flask(__name__)
app.secret_key = "dev-secret-key-change-this"  # change for production
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(APP_DIR, "ecommerce.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database models
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(400))
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(400), nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    email = db.Column(db.String(200), unique=True)
    password = db.Column(db.String(200))  # plaintext for demo—DO NOT do this in production

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, default=1)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(400))
    phone = db.Column(db.String(50))
    status = db.Column(db.String(50), default="placed")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, default=1)

# Create DB and add sample data if empty
# Inside app.app_context() after db.create_all()
with app.app_context():
    db.create_all()

    # Automatically create products for all images in static/img
    img_files = [f for f in os.listdir(IMG_DIR) if f.lower().endswith((".png", ".jpg", ".jpeg"))]

    for img_name in img_files:
        # Check if a product for this image already exists
        img_url = f"/static/img/{img_name}"
        if not Product.query.filter_by(image_url=img_url).first():
            # Use filename (without extension) as product name
            name = os.path.splitext(img_name)[0].replace("_", " ").title()
            p = Product(name=name, price=499.0, description=f"Demo product: {name}", image_url=img_url)
            db.session.add(p)
    db.session.commit()


# Helper functions
def current_cart_count():
    uid = session.get("user_id")
    if not uid:
        return 0
    items = CartItem.query.filter_by(user_id=uid).all()
    return sum([i.quantity for i in items])

@app.context_processor
def inject_cart_count():
    return dict(cart_count=current_cart_count())

# Routes
@app.route("/")
def index():
    products = Product.query.all()
    return render_template("index.html", products=products)

@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    results = []
    if q:
        results = Product.query.filter(Product.name.ilike(f"%{q}%") | Product.description.ilike(f"%{q}%")).all()
    return render_template("search.html", results=results, query=q)

@app.route("/product/<int:pid>")
def product_view(pid):
    p = Product.query.get_or_404(pid)
    return render_template("product.html", product=p)

# Admin - add product
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        name = request.form.get("name")
        price = request.form.get("price")
        description = request.form.get("description")
        image = request.files.get("image")
        if not (name and price and image):
            flash("Missing fields.")
            return redirect(url_for("admin"))
        filename = secure_filename(image.filename)
        if filename == "":
            flash("Invalid filename.")
            return redirect(url_for("admin"))
        dest = os.path.join(IMG_DIR, filename)
        image.save(dest)
        img_url = f"/static/img/{filename}"
        newp = Product(name=name, price=float(price), description=description, image_url=img_url)
        db.session.add(newp)
        db.session.commit()
        flash("Product added.")
        return redirect(url_for("admin"))
    products = Product.query.order_by(Product.id.desc()).all()
    return render_template("admin.html", products=products)

@app.route("/delete_product/<int:pid>")
def delete_product(pid):
    p = Product.query.get(pid)
    if p:
        db.session.delete(p)
        db.session.commit()
        flash("Product deleted.")
    return redirect(url_for("admin"))

@app.route("/edit_product/<int:pid>", methods=["GET", "POST"])
def edit_product(pid):
    p = Product.query.get_or_404(pid)

    if request.method == "POST":
        p.name = request.form.get("name")
        p.price = float(request.form.get("price"))
        p.description = request.form.get("description")

        new_image = request.files.get("image")
        if new_image and new_image.filename != "":
            filename = secure_filename(new_image.filename)
            dest = os.path.join(IMG_DIR, filename)
            new_image.save(dest)
            p.image_url = f"/static/img/{filename}"

        db.session.commit()
        flash("Product updated.")
        return redirect(url_for("admin"))

    return render_template("edit_product.html", product=p)




# Auth
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        pw = request.form.get("password")
        pw2 = request.form.get("password2")
        if pw != pw2:
            flash("Passwords do not match.")
            return redirect(url_for("register"))
        if User.query.filter_by(email=email).first():
            flash("Email already exists.")
            return redirect(url_for("register"))
        u = User(name=name, email=email, password=pw)
        db.session.add(u)
        db.session.commit()
        session['user_id'] = u.id
        flash("Registered & logged in.")
        return redirect(url_for("index"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        pw = request.form.get("password")
        u = User.query.filter_by(email=email, password=pw).first()
        if not u:
            flash("Invalid login.")
            return redirect(url_for("login"))
        session['user_id'] = u.id
        flash("Logged in.")
        return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logged out.")
    return redirect(url_for("index"))

# Cart routes
@app.route("/add_to_cart/<int:pid>")
def add_to_cart(pid):
    uid = session.get("user_id")
    if not uid:
        flash("Please login first.")
        return redirect(url_for("login"))
    # If item exists, increment quantity else create
    it = CartItem.query.filter_by(user_id=uid, product_id=pid).first()
    if it:
        it.quantity += 1
    else:
        it = CartItem(user_id=uid, product_id=pid, quantity=1)
        db.session.add(it)
    db.session.commit()
    flash("Added to cart.")
    return redirect(url_for("cart"))

@app.route("/cart")
def cart():
    uid = session.get("user_id")
    if not uid:
        flash("Please login to view cart.")
        return redirect(url_for("login"))
    items = CartItem.query.filter_by(user_id=uid).all()
    # attach product object to each for template convenience
    class Wrapper: pass
    wrapped = []
    total = 0.0
    for it in items:
        w = Wrapper()
        w.product = Product.query.get(it.product_id)
        w.quantity = it.quantity
        total += w.product.price * it.quantity
        wrapped.append(w)
    return render_template("cart.html", items=wrapped, total=total)

@app.route("/remove_from_cart/<int:pid>")
def remove_from_cart(pid):
    uid = session.get("user_id")
    if not uid:
        flash("Please login.")
        return redirect(url_for("login"))
    it = CartItem.query.filter_by(user_id=uid, product_id=pid).first()
    if it:
        db.session.delete(it)
        db.session.commit()
        flash("Removed from cart.")
    return redirect(url_for("cart"))

# Checkout (POST triggers payment)
@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    uid = session.get("user_id")
    if not uid:
        flash("Please login.")
        return redirect(url_for("login"))
    items = CartItem.query.filter_by(user_id=uid).all()
    if not items:
        flash("Cart is empty.")
        return redirect(url_for("cart"))
    total = 0.0
    for it in items:
        p = Product.query.get(it.product_id)
        total += p.price * it.quantity

    # If POST -> process payment (simulated or via Stripe if configured)
    if request.method == "POST":
        address = request.form.get("address")
        phone = request.form.get("phone")
        # Stripe integration if available + keys
        stripe_secret = os.environ.get("STRIPE_SECRET_KEY")
        stripe_pub = os.environ.get("STRIPE_PUBLISHABLE_KEY")
        if STRIPE_AVAILABLE and stripe_secret and stripe_pub:
            try:
                stripe.api_key = stripe_secret
                # Create a PaymentIntent for the total amount (in smallest currency unit)
                amount_minor = int(total * 100)  # e.g. rupees -> paise
                intent = stripe.PaymentIntent.create(
                    amount=amount_minor,
                    currency="inr",
                    payment_method_types=["card"],
                    metadata={"user_id": str(uid)}
                )
                # create order with status 'pending'
                order = Order(user_id=uid, total=total, address=address, phone=phone, status="pending")
                db.session.add(order)
                db.session.commit()
                # save items
                for it in items:
                    oi = OrderItem(order_id=order.id, product_id=it.product_id, quantity=it.quantity)
                    db.session.add(oi)
                # clear cart
                for it in items:
                    db.session.delete(it)
                db.session.commit()
                # Return client secret to front-end or redirect (we'll just show a simple message)
                flash("PaymentIntent created in Stripe test mode. (Simulated redirect step.)")
                return redirect(url_for("orders"))
            except Exception as e:
                flash("Stripe error: " + str(e))
                return redirect(url_for("checkout"))

        # Simulated payment flow (default)
        order = Order(user_id=uid, total=total, address=address, phone=phone, status="placed")
        db.session.add(order)
        db.session.commit()
        for it in items:
            oi = OrderItem(order_id=order.id, product_id=it.product_id, quantity=it.quantity)
            db.session.add(oi)
            db.session.delete(it)  # clear cart
        db.session.commit()
        flash("Payment simulated — order placed!")
        return redirect(url_for("orders"))

    # GET -> show checkout page
    simulate = not (STRIPE_AVAILABLE and os.environ.get("STRIPE_SECRET_KEY") and os.environ.get("STRIPE_PUBLISHABLE_KEY"))
    return render_template("checkout.html", total=total, simulate=simulate)

@app.route("/orders")
def orders():
    uid = session.get("user_id")
    if not uid:
        flash("Please login.")
        return redirect(url_for("login"))
    orders = Order.query.filter_by(user_id=uid).order_by(Order.created_at.desc()).all()
    # attach items and products for template display
    grouped = []
    for o in orders:
        o.items = OrderItem.query.filter_by(order_id=o.id).all()
        for it in o.items:
            it.product = Product.query.get(it.product_id)
        grouped.append(o)
    return render_template("orders.html", orders=grouped)

# Small API endpoints
@app.route("/api/products")
def api_products():
    prods = Product.query.all()
    out = [{"id":p.id,"name":p.name,"price":p.price,"image":p.image_url} for p in prods]
    return jsonify(out)

# Run
if __name__ == "__main__":
    # helpful message about where the uploaded demo image came from
    if os.path.exists(UPLOADED_IMAGE_PATH):
        print("Copied demo image from:", UPLOADED_IMAGE_PATH, "-> static/img/product_demo.jpg")
    else:
        print("No uploaded demo image found at", UPLOADED_IMAGE_PATH)
    print(" * Running on http://127.0.0.1:8001")
    app.run(host="127.0.0.1", port=8001, debug=False, use_reloader=False)
