"""
notify.py

Sends an automated alert to the matched NGO once a match is found.

For the MVP/demo, this logs the notification to a local file instead of
sending a real SMS/email/WhatsApp message — that keeps the demo free to run
with no API keys required. The function signature is written so swapping in
a real provider (Twilio, SendGrid, etc.) later only touches this one file.
"""

import os
from datetime import datetime

LOG_PATH = os.path.join(os.path.dirname(__file__), "data", "notifications.log")


def send_notification(ngo, listing, match_result):
    """
    ngo: dict with at least 'name'
    listing: dict with 'food_type', 'quantity_kg', 'vendor_location'
    match_result: dict returned by matching_engine.find_best_match

    Returns the message string that was "sent", so the caller can also
    display it in the UI for the demo.
    """
    message = (
        f"[ALERT] {ngo['name']}: A vendor at {listing.get('vendor_location', 'unknown location')} "
        f"has {listing['quantity_kg']}kg of {listing['food_type']} available for pickup, "
        f"expiring in {listing['expiry_hours']}h. "
        f"Distance: {match_result['distance_km']}km. Please confirm pickup."
    )

    timestamp = datetime.now().isoformat(timespec="seconds")
    with open(LOG_PATH, "a") as f:
        f.write(f"{timestamp} | {message}\n")

    # --- To go live later, replace the block above with something like: ---
    # from twilio.rest import Client
    # client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    # client.messages.create(body=message, from_=TWILIO_NUMBER, to=ngo["phone"])

    return message


def send_community_alert(subscriber, listing):
    """
    subscriber: dict with 'name', 'contact', 'location'
    listing: the sell-listing dict just posted to the public board

    Same demo-logging approach as send_notification -- logs instead of
    sending a real SMS/WhatsApp message, so this runs with no API keys.
    """
    message = (
        f"[COMMUNITY ALERT] Hi {subscriber['name']}, {listing['vendor_name']} just listed "
        f"{listing['quantity_kg']}kg of {listing['food_type']} for {listing['sale_price']} "
        f"in {subscriber['location']}. Good for {listing['expiry_hours']}h. "
        f"Contact {listing['vendor_contact']} to reserve."
    )

    timestamp = datetime.now().isoformat(timespec="seconds")
    with open(LOG_PATH, "a") as f:
        f.write(f"{timestamp} | {message}\n")

    return message