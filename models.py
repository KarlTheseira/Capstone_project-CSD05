from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price_cents = db.Column(db.Integer, nullable=False)  # store in smallest currency unit
    media_key = db.Column(db.String(512), nullable=False)  # filename or blob name
    mime_type = db.Column(db.String(128))
    thumbnail_key = db.Column(db.String(512))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    stock = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(128), nullable=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    amount_cents = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(16), nullable=False, default="usd")
    stripe_payment_intent = db.Column(db.String(255))
    status = db.Column(db.String(32), default="created")  # created, paid, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User", backref="orders")

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    unit_price_cents = db.Column(db.Integer, nullable=False)

    order = db.relationship("Order", backref=db.backref("items", lazy=True))
    product = db.relationship("Product")

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)  # optional

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
