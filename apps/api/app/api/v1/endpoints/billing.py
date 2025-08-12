from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import stripe

from app.api.deps import get_current_user, get_db
from app.core.config import get_settings
from app.models.user import User

router = APIRouter()


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

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url="http://localhost:3000/dashboard?checkout=success",
            cancel_url="http://localhost:3000/dashboard?checkout=cancel",
            client_reference_id=str(current_user.id),
            customer_email=current_user.email,
        )
        return {"checkout_url": session.url}
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

    if event["type"] in {"checkout.session.completed", "customer.subscription.updated", "customer.subscription.created"}:
        data = event["data"]["object"]
        client_ref = data.get("client_reference_id") or data.get("metadata", {}).get("user_id")
        if client_ref:
            user = db.query(User).filter(User.id == client_ref).first()
            if user:
                price_id = None
                if "lines" in data and data["lines"]["data"]:
                    price_id = data["lines"]["data"][0]["price"]["id"]
                elif "subscription" in data and data["subscription"]:
                    pass
                plan_name = None
                settings = get_settings()
                if price_id == settings.stripe_price_basic:
                    plan_name = "Basic"
                elif price_id == settings.stripe_price_pro:
                    plan_name = "Pro"
                elif price_id == settings.stripe_price_premium:
                    plan_name = "Premium"
                if plan_name:
                    user.plan_id = plan_name
                    db.add(user)
                    db.commit()
    return JSONResponse(status_code=200, content={"received": True}) 