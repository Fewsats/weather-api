import os
from fewsats.core import *
from replit import db
from users import get_user, save_user, User

fewsats_api_key = os.getenv("FEWSATS_API_KEY")
if not fewsats_api_key:
    raise ValueError("FEWSATS_API_KEY is not set")

fs = Fewsats(api_key=fewsats_api_key)

offers = [
    {
        "id": "offer_1",
        "title": "1 credit package",
        "description": "Add 1 credit to your account.",
        "amount": 1,  # Price in USD Cents
        "currency": "USD",
        "payment_methods":
        ["lightning"]  # Each offer can support different payment methods
    },
    {
        "id": "offer_2",
        "title": "1000 credit package",
        "description": "Add 1000 credits to your account.",
        "amount": 500,  # Price in USD Cents
        "currency": "USD",
        "payment_methods":
        ["lightning",
         "credit_card"]  # One offer can support multiple payment methods
    },
]


def create_payment_information(current_user_id):
    """
    Create L402 response for the available offers
    """
    # Create the L402 response body with information about the offers and how to pay
    offers_information = fs.create_offers(offers)
    offers_information.raise_for_status()

    # Store the payment context token with the user ID
    # So we can credit the user when they pay (we will receive a webhook from Fewsats)
    payment_context_token = offers_information.json().get(
        "payment_context_token")
    db[f"payment:{payment_context_token}"] = current_user_id

    return offers_information


def webhook(payload):
    """
    Webhook for Fewsats payment events
    """
    # Verify payment status
    if payload.status != "success":
        return {
            "status": "error",
            "message": f"Payment status is {payload.status}, not completed"
        }

    # Get the user ID associated with this payment context token
    user_id = db.get(f"payment:{payload.payment_context_token}")
    if not user_id:
        return {
            "status": "error",
            "message": "Payment context token not found"
        }

    # Get the user
    user = get_user(user_id)
    if not user:
        return {"status": "error", "message": "User not found"}

    # Add credits based on the offer ID
    if payload.offer_id == "offer_1":
        user.credits += 1
    elif payload.offer_id == "offer_2":
        user.credits += 1000
    else:
        return {
            "status": "error",
            "message": f"Unknown offer ID: {payload.offer_id}"
        }

    # Save updated user
    save_user(user)

    # Clean up the payment context token
    if f"payment:{payload.payment_context_token}" in db:
        del db[f"payment:{payload.payment_context_token}"]

    return {"status": "success", "user_id": user_id, "credits": user.credits}
