from flask import Blueprint, render_template, request
from models import Product, db

public_bp = Blueprint('public', __name__)

@public_bp.route("/")
def index():
    q          = request.args.get("q", "").strip()
    min_price  = request.args.get("min_price", type=int)
    max_price  = request.args.get("max_price", type=int)
    category   = request.args.get("category", "").strip()
    media_type = request.args.get("media_type", "").strip()

    products_q = Product.query

    if q:
        products_q = products_q.filter(Product.title.ilike(f"%{q}%"))
    if min_price is not None:
        products_q = products_q.filter(Product.price_cents >= min_price * 100)
    if max_price is not None:
        products_q = products_q.filter(Product.price_cents <= max_price * 100)
    if category:
        products_q = products_q.filter_by(category=category)
    if media_type:
        products_q = products_q.filter(Product.mime_type.ilike(f"{media_type}%"))

    products = products_q.order_by(Product.created_at.desc()).all()

    categories  = [c[0] for c in db.session.query(Product.category).distinct() if c[0]]
    media_types = [m[0] for m in db.session.query(Product.mime_type).distinct() if m[0]]

    return render_template(
        "index.html",
        products=products,
        categories=categories,
        media_types=media_types,
        filters={
            "q": q,
            "min_price": min_price,
            "max_price": max_price,
            "category": category,
            "media_type": media_type,
        }
    )

@public_bp.route("/product/<int:product_id>")
def product(product_id):
    p = Product.query.get_or_404(product_id)
    return render_template("product.html", product=p)
