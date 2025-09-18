from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort
from models import Product, Order, db
from utils.media import save_media
from config import Config

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def require_admin():
    if not session.get("admin"):
        abort(403)

@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("admin_login.html")

    username = request.form.get("username")
    password = request.form.get("password")

    if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
        session["admin"] = True
        return redirect(url_for("admin.dashboard"))

    return render_template("admin_login.html", error="Invalid credentials")

@admin_bp.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("admin.login"))

@admin_bp.route("/", methods=["GET", "POST"])
def dashboard():
    require_admin()

    if request.method == "POST":
        title       = request.form.get("title")
        description = request.form.get("description")
        price_cents = int(float(request.form.get("price", 0)) * 100)
        file        = request.files.get("media")
        thumb       = request.files.get("thumbnail")
        stock       = int(request.form.get("stock", 0))

        if not title or not file:
            return render_template(
                "admin_dashboard.html",
                error="Title and media file are required.",
                products=Product.query.order_by(Product.created_at.desc()).all()
            )

        media_key, _url = save_media(file)
        thumbnail_key = None
        if thumb:
            thumbnail_key, _ = save_media(thumb)

        product = Product(
            title=title,
            description=description,
            price_cents=price_cents,
            media_key=media_key,
            mime_type=file.mimetype,
            thumbnail_key=thumbnail_key,
            stock=stock
        )
        db.session.add(product)
        db.session.commit()
        flash("Product added successfully.", "success")
        return redirect(url_for("admin.dashboard"))

    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template("admin_dashboard.html", products=products)

@admin_bp.route("/update_stock/<int:product_id>", methods=["POST"])
def update_stock(product_id):
    require_admin()
    product = Product.query.get_or_404(product_id)
    new_stock = request.form.get("stock")

    try:
        product.stock = int(new_stock)
        db.session.commit()
        flash("Stock updated successfully.", "success")
    except (ValueError, TypeError):
        flash("Invalid stock value.", "danger")

    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/delete/<int:product_id>", methods=["POST"])
def delete(product_id):
    require_admin()
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted successfully.", "success")
    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/edit/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    require_admin()
    product = Product.query.get_or_404(product_id)

    if request.method == "POST":
        # basic fields
        product.title = request.form.get("title", "").strip()
        product.description = request.form.get("description", "").strip()
        product.stock = request.form.get("stock", type=int) or 0

        # price -> cents
        price = request.form.get("price", type=float)
        if price is not None:
            product.price_cents = int(round(price * 100))

        # optional category
        product.category = request.form.get("category", "").strip() or product.category

        # optional file updates
        file = request.files.get("media")
        thumb = request.files.get("thumbnail")

        if file and file.filename:
            media_key, _url = save_media(file)
            product.media_key = media_key
            product.mime_type = file.mimetype

        if thumb and thumb.filename:
            thumbnail_key, _ = save_media(thumb)
            product.thumbnail_key = thumbnail_key

        db.session.commit()
        flash("Product updated.", "success")
        return redirect(url_for("admin.dashboard"))

    # GET -> render edit form
    return render_template("admin_product_edit.html", product=product)

@admin_bp.route("/orders")
def orders():
    require_admin()
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template("admin_orders.html", orders=orders)

@admin_bp.route("/orders/<int:order_id>", methods=["GET", "POST"])
def order_detail(order_id):
    require_admin()
    order = Order.query.get_or_404(order_id)

    if request.method == "POST":
        new_status = request.form.get("status")
        if new_status:
            order.status = new_status
            db.session.commit()
            flash("Order status updated.", "success")
        return redirect(url_for("admin.orders"))

    return render_template("admin_order_detail.html", order=order)
