import stripe
from flask import current_app, url_for

def init_stripe():
    stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]

def create_checkout_session(items, customer_email: str):
    """
    items: list of dicts {name, quantity, unit_amount, currency}
    Returns Stripe Checkout Session URL and payment_intent id.
    """
    init_stripe()
    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        customer_email=customer_email,
        line_items=[
            {
                "price_data": {
                    "currency": i["currency"],
                    "unit_amount": i["unit_amount"],
                    "product_data": {"name": i["name"]},
                },
                "quantity": i["quantity"],
            }
            for i in items
        ],
        success_url=url_for("success", _external=True) + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=url_for("cart", _external=True),
    )
    return session.url, session.payment_intent
