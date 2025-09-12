import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort, send_file
from config import Config
from models import db, Product, Order, OrderItem
from services.storage import save_media, serve_local_media, generate_download_url
from services.payments import create_checkout_session
from utils.signing import create_signed_token, verify_signed_token
import stripe
from io import BytesIO

load_dotenv()

def create_app():
    app = Flask(__name__, static_folder="static")
    app.config.from_object(Config)

    db.init_app(app)

    @app.cli.command("init-db")
    def init_db_command():
        with app.app_context():
            db.create_all()
            print("Database initialized.")

    # Public pages
    @app.route("/")
    def index():
        products = Product.query.order_by(Product.created_at.desc()).all()
        return render_template("index.html", products=products)

    @app.route("/product/<int:product_id>")
    def product(product_id):
        p = Product.query.get_or_404(product_id)
        return render_template("product.html", product=p)

    # Cart in session
    @app.route("/cart")
    def cart():
        cart = session.get("cart", {})
        ids = [int(i) for i in cart.keys()]
        products = Product.query.filter(Product.id.in_(ids)).all() if ids else []
        items = []
        total = 0
        for p in products:
            qty = cart.get(str(p.id), 1)
            line = {"product": p, "qty": qty, "subtotal": p.price_cents * qty}
            items.append(line)
            total += line["subtotal"]
        return render_template("cart.html", items=items, total=total)

    @app.post("/cart/add/<int:product_id>")
    def cart_add(product_id):
        Product.query.get_or_404(product_id)
        cart = session.get("cart", {})
        cart[str(product_id)] = cart.get(str(product_id), 0) + int(request.form.get("qty", 1))
        session["cart"] = cart
        return redirect(url_for("cart"))

    @app.post("/cart/remove/<int:product_id>")
    def cart_remove(product_id):
        cart = session.get("cart", {})
        cart.pop(str(product_id), None)
        session["cart"] = cart
        return redirect(url_for("cart"))

    # Checkout
    @app.route("/checkout", methods=["GET", "POST"])
    def checkout():
        if request.method == "GET":
            return render_template("checkout.html")
        email = request.form.get("email")
        cart = session.get("cart", {})
        if not cart:
            return redirect(url_for("cart"))

        ids = [int(i) for i in cart.keys()]
        products = Product.query.filter(Product.id.in_(ids)).all()
        items = []
        total = 0
        for p in products:
            qty = int(cart[str(p.id)])
            total += p.price_cents * qty
            items.append({
                "name": p.title,
                "quantity": qty,
                "unit_amount": p.price_cents,
                "currency": Config.CURRENCY,
            })

        # Pre-create order
        order = Order(email=email, amount_cents=total, currency=Config.CURRENCY)
        db.session.add(order)
        db.session.flush()
        for p in products:
            qty = int(cart[str(p.id)])
            db.session.add(OrderItem(order_id=order.id, product_id=p.id, quantity=qty, unit_price_cents=p.price_cents))
        db.session.commit()

        url, pi = create_checkout_session(items, email)
        order.stripe_payment_intent = pi
        db.session.commit()

        session["pending_order_id"] = order.id
        return redirect(url)

    @app.route("/success")
    def success():
        session.pop("cart", None)
        return render_template("success.html")

    # Stripe webhook
    @app.post("/webhook/stripe")
    def stripe_webhook():
        wh_secret = Config.STRIPE_WEBHOOK_SECRET
        payload = request.data
        sig = request.headers.get("Stripe-Signature", "")
        try:
            event = stripe.Webhook.construct_event(payload=payload, sig_header=sig, secret=wh_secret)
        except Exception:
            return "bad", 400

        if event["type"] == "checkout.session.completed":
            pi = event["data"]["object"]["payment_intent"]
            order = Order.query.filter_by(stripe_payment_intent=pi).first()
            if order:
                order.status = "paid"
                db.session.commit()
        return "ok", 200

    # Download links (post-purchase)
    @app.route("/my-downloads")
    def my_downloads():
        # In a real app you'd require login; here we accept email param for simplicity.
        email = request.args.get("email")
        if not email:
            abort(400)
        orders = Order.query.filter_by(email=email, status="paid").all()
        products = []
        for o in orders:
            for item in o.items:
                products.append(item.product)

        links = []
        for p in products:
            if Config.STORAGE_BACKEND == "local":
                token = create_signed_token(p.media_key)
                links.append({"title": p.title, "url": url_for("download_signed", token=token, _external=False)})
            else:
                links.append({"title": p.title, "url": generate_download_url(p.media_key)})
        return render_template("success.html", links=links)  # reuse success template to show links

    @app.route("/download")
    def download_signed():
        token = request.args.get("token")
        key = verify_signed_token(token, 3600)
        if not key:
            abort(403)
        # local only; for Azure we return SAS directly
        return serve_local_media(key)

    # Serve local media (only in local backend)
    @app.route("/media/<path:filename>")
    def media(filename):
        if Config.STORAGE_BACKEND != "local":
            abort(404)
        return serve_local_media(filename)

    # Admin
    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if request.method == "GET":
            return render_template("admin_login.html")
        u = request.form.get("username")
        p = request.form.get("password")
        if u == Config.ADMIN_USERNAME and p == Config.ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        return render_template("admin_login.html", error="Invalid credentials")

    @app.route("/admin/logout")
    def admin_logout():
        session.pop("admin", None)
        return redirect(url_for("admin_login"))

    def require_admin():
        if not session.get("admin"):
            abort(403)

    @app.route("/admin", methods=["GET", "POST"])
    def admin_dashboard():
        require_admin()
        if request.method == "POST":
            title = request.form.get("title")
            description = request.form.get("description")
            price = int(float(request.form.get("price")) * 100)
            file = request.files.get("media")
            if not (title and file):
                return render_template("admin_dashboard.html", error="Title and file are required.", products=Product.query.all())
            media_key, _url = save_media(file)
            product = Product(title=title, description=description, price_cents=price, media_key=media_key, mime_type=file.mimetype)
            db.session.add(product)
            db.session.commit()
            return redirect(url_for("admin_dashboard"))
        return render_template("admin_dashboard.html", products=Product.query.order_by(Product.created_at.desc()).all())

    return app

app = create_app()
