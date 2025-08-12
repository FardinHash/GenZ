from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import stripe

from app.api.deps import get_current_user, get_db
from app.core.config import get_settings
from app.models.user import User

router = APIRouter()


def _get_billing_settings(user: User) -> dict:
    current = user.settings or {}
    billing = current.get("billing") or {}
    current["billing"] = billing
    user.settings = current
    return billing


@router.post("/subscribe")
async def subscribe(plan: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    settings = get_settings()
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    stripe.api_key = settings.stripe_secret_key

    price_map = {
        "Basic": settings.stripe_price_basic,
        "Pro": settings.stripe_price_pro,
        "Premium": settings.stripe_price_premium,
    }
    price_id = price_map.get(plan)
    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid plan")

    billing = _get_billing_settings(current_user)
    customer_id = billing.get("stripe_customer_id")
    if not customer_id:
        try:
            customer = stripe.Customer.create(email=current_user.email, metadata={"user_id": str(current_user.id)})
            billing["stripe_customer_id"] = customer.id
            db.add(current_user)
            db.commit()
            customer_id = customer.id
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create customer: {e}")

    try:
        params = dict(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url="http://localhost:3000/dashboard?checkout=success",
            cancel_url="http://localhost:3000/dashboard?checkout=cancel",
            client_reference_id=str(current_user.id),
            allow_promotion_codes=True,
            subscription_data={"metadata": {"user_id": str(current_user.id)}},
            customer=customer_id,
        )
        if not customer_id:
            params.pop("customer")
            params["customer_email"] = current_user.email

        session = stripe.checkout.Session.create(**params)
        return {"checkout_url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portal")
async def create_billing_portal(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    settings = get_settings()
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    stripe.api_key = settings.stripe_secret_key

    billing = _get_billing_settings(current_user)
    customer_id = billing.get("stripe_customer_id")
    if not customer_id:
        try:
            candidates = stripe.Customer.search(query=f"email:'{current_user.email}'")
            cust = candidates.data[0] if candidates.data else stripe.Customer.create(email=current_user.email, metadata={"user_id": str(current_user.id)})
            billing["stripe_customer_id"] = cust.id
            db.add(current_user)
            db.commit()
            customer_id = cust.id
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"No Stripe customer on file and lookup failed: {e}")

    try:
        sess = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url="http://localhost:3000/dashboard",
        )
        return {"portal_url": sess.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    settings = get_settings()
    if not settings.stripe_webhook_secret:
        return JSONResponse(status_code=200, content={"received": True})

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(
            payload=payload, sig_header=sig_header, secret=settings.stripe_webhook_secret
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    def set_plan_from_price(user: User, price_id: str | None):
        name = None
        if price_id == settings.stripe_price_basic:
            name = "Basic"
        elif price_id == settings.stripe_price_pro:
            name = "Pro"
        elif price_id == settings.stripe_price_premium:
            name = "Premium"
        if name:
            user.plan_id = name

    etype = event["type"]
    data = event["data"]["object"]

    if etype == "checkout.session.completed":
        user = None
        uid = data.get("client_reference_id")
        if uid:
            user = db.query(User).filter(User.id == uid).first()
        if user:
            billing = _get_billing_settings(user)
            if data.get("customer"):
                billing["stripe_customer_id"] = data.get("customer")
            if data.get("subscription"):
                billing["stripe_subscription_id"] = data.get("subscription")
            price_id = None
            if data.get("line_items") and data["line_items"]["data"]:
                price_id = data["line_items"]["data"][0]["price"]["id"]
            set_plan_from_price(user, price_id)
            db.add(user)
            db.commit()

    elif etype in {"customer.subscription.created", "customer.subscription.updated"}:
        sub = data
        uid = (sub.get("metadata") or {}).get("user_id")
        user = None
        if uid:
            user = db.query(User).filter(User.id == uid).first()
        if not user:
            cust_id = sub.get("customer")
            if cust_id:
                user = db.query(User).filter(User.settings["billing"]["stripe_customer_id"].astext == cust_id).first()  # type: ignore
        if user:
            billing = _get_billing_settings(user)
            if sub.get("customer"):
                billing["stripe_customer_id"] = sub.get("customer")
            billing["stripe_subscription_id"] = sub.get("id")
            status_val = sub.get("status")
            cancel_at_period_end = bool(sub.get("cancel_at_period_end"))
            if status_val == "canceled" or cancel_at_period_end:
                user.plan_id = "Basic"
            else:
                price_id = None
                items = (sub.get("items") or {}).get("data") or []
                if items:
                    price_id = items[0]["price"]["id"]
                set_plan_from_price(user, price_id)
            db.add(user)
            db.commit()

    elif etype == "customer.subscription.deleted":
        sub = data
        uid = (sub.get("metadata") or {}).get("user_id")
        user = None
        if uid:
            user = db.query(User).filter(User.id == uid).first()
        if not user:
            cust_id = sub.get("customer")
            if cust_id:
                user = db.query(User).filter(User.settings["billing"]["stripe_customer_id"].astext == cust_id).first()  # type: ignore
        if user:
            billing = _get_billing_settings(user)
            billing["stripe_subscription_id"] = None
            user.plan_id = "Basic"
            db.add(user)
            db.commit()

    return JSONResponse(status_code=200, content={"received": True})