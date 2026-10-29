"""
WhatsApp Interactive Confirmation & Nudge State Machine
Mocks the automated customer conversation flows for:
1. "Ship after confirmation"
2. "Nudge to prepaid"

Handles affirmative replies ("yes", "1"), negative ("no", "2"),
unstructured/random queries with NLP intent matching, and 24-hour timeout schedules.
"""

from datetime import datetime, timedelta

class WhatsAppStateMachine:
    def __init__(self, discount_amount=60.0):
        self.discount_amount = discount_amount

    def generate_initial_message(self, flow_type: str, order: dict) -> dict:
        """Generates outgoing message, language template, and dispatch timing."""
        name = order.get("customer_name", "Valued Customer")
        order_id = order.get("order_id", "ORD-XXXX")
        prod = order.get("product_name", "Haircare Essentials")
        amount = float(order.get("order_value", 649.0))
        address = order.get("shipping_address", "")
        city = order.get("city", "")
        pin = order.get("pincode", "")

        if flow_type == "Ship after confirmation":
            message_text = (
                f"Namaste {name}! 🌿\n\n"
                f"Thank you for ordering with us!\n"
                f"📦 *Order #{order_id}*: {prod}\n"
                f"💵 *Amount to Pay on Delivery*: ₹{amount:,.0f}\n"
                f"📍 *Shipping To*: {address}, {city} - {pin}\n\n"
                f"To ensure smooth doorstep delivery and prevent delays, please confirm your order:\n\n"
                f"👉 Reply *1* or *YES* to Confirm Delivery\n"
                f"👉 Reply *2* or *NO* to Cancel Order"
            )
            dispatch_time = "T+5 minutes after order creation (pre-warehouse batching)"
            trigger_reason = "Moderate risk score or first-time buyer verification"

        elif flow_type == "Nudge to prepaid":
            pay_now_amount = max(0.0, amount - self.discount_amount)
            message_text = (
                f"Namaste {name}! 🌿\n\n"
                f"We are packing your order *#{order_id}* ({prod})!\n\n"
                f"⚡ *EXCLUSIVE PREPAID PRIVILEGE*:\n"
                f"Pay online right now and save *FLAT ₹{self.discount_amount:,.0f}*!\n\n"
                f"❌ COD Price: ₹{amount:,.0f}\n"
                f"✅ *Prepaid VIP Price: ₹{pay_now_amount:,.0f}* (Instant ₹{self.discount_amount:,.0f} OFF)\n"
                f"🚀 *Bonus*: Priority 24-hour dispatch & contact-free delivery.\n\n"
                f"👉 Reply *1* to Pay Online (Instant UPI / GPay / Card Link)\n"
                f"👉 Reply *2* to Continue with Cash on Delivery (COD)\n"
                f"👉 Reply *3* to Cancel Order"
            )
            dispatch_time = "T+10 minutes after order creation"
            trigger_reason = "High-ticket COD order or remote zone; incentivizes online prepayment"
        else:
            message_text = f"Order #{order_id} update."
            dispatch_time = "Immediate"
            trigger_reason = "Standard notification"

        return {
            "flow_type": flow_type,
            "order_id": order_id,
            "scheduled_time": dispatch_time,
            "trigger_reason": trigger_reason,
            "language": "Hinglish / Conversational Indian English",
            "message_text": message_text,
            "current_state": "WAITING_FOR_REPLY",
            "created_at": datetime.now().isoformat()
        }

    def process_reply(self, flow_type: str, incoming_text: str, current_state: str, order: dict) -> dict:
        """Processes customer reply (yes/no/random) and transitions state."""
        text = (incoming_text or "").strip().lower()

        # Affirmative patterns
        yes_keywords = ["1", "yes", "haan", "ha", "confirm", "ship", "bhej do", "sahi hai", "ok", "done", "plz send"]
        # Negative patterns
        no_keywords = ["2", "no", "nahi", "cancel", "mat bhejo", "don't send", "cancel it", "galti se hua", "stop"]
        # Continue COD patterns (for prepaid flow)
        keep_cod_keywords = ["2", "cod", "cash", "keep cod", "cod hi rakho"]

        if flow_type == "Ship after confirmation":
            if any(k == text or k in text.split() for k in yes_keywords):
                new_state = "CONFIRMED_FOR_DISPATCH"
                bot_reply = (
                    "Thank you so much! 🎉 Your order is confirmed and assigned to our priority packaging queue. "
                    "We will share live tracking as soon as it leaves the warehouse!"
                )
                action_taken = "Order status updated to APPROVED. Forwarded to warehouse WMS."
            elif any(k == text or k in text.split() for k in no_keywords):
                new_state = "CANCELLED_BY_CUSTOMER"
                bot_reply = (
                    "Your order has been cancelled as requested. 🙏 No charges were made. "
                    "If you ever need haircare recommendations, we're always here for you!"
                )
                action_taken = "Order cancelled before fulfillment. Inventory restocked. Saved ₹169.40 RTO cost."
            else:
                # Random / Unstructured Query
                new_state = "AWAITING_CLARIFICATION"
                bot_reply = self._handle_random_query(incoming_text)
                action_taken = "Query handled with NLP. Re-prompted for confirmation."

        elif flow_type == "Nudge to prepaid":
            pay_keywords = ["1", "pay", "pay online", "upi", "link", "gpay", "online", "card", "qr"]
            cancel_keywords = ["3", "cancel", "cancel order", "nahi", "mat bhejo"]
            if any(k in text for k in pay_keywords) and not any(c in text for c in cancel_keywords):
                new_state = "PREPAID_LINK_SENT"
                amount = float(order.get("order_value", 649.0))
                pay_now = max(0.0, amount - self.discount_amount)
                bot_reply = (
                    f"Awesome! 🌟 Here is your secure payment link for ₹{pay_now:,.0f} (₹{self.discount_amount:,.0f} OFF):\n"
                    f"🔗 https://pay.haircarebrand.com/upi/{order.get('order_id', '123')}?amt={pay_now}\n\n"
                    f"Once payment completes, we immediately tag your parcel for Priority Express delivery!"
                )
                action_taken = "Payment gateway link dispatched. RTO risk drops to 4% upon payment."
            elif any(c in text for c in cancel_keywords):
                new_state = "CANCELLED_BY_CUSTOMER"
                bot_reply = "Your order has been cancelled. Thank you for letting us know! 🙏"
                action_taken = "Order cancelled cleanly without logistics penalty."
            elif any(k in text for k in keep_cod_keywords):
                new_state = "PROCEED_WITH_COD"
                bot_reply = (
                    "Understood! We will dispatch your order with Cash on Delivery (COD). "
                    "Please keep exact cash ready at delivery! 🚚"
                )
                action_taken = "Customer opted out of discount. Shipped under COD protocol."
            else:
                new_state = "AWAITING_CLARIFICATION"
                bot_reply = self._handle_random_query(incoming_text)
                action_taken = "Query answered. Re-sent options."

        return {
            "incoming_text": incoming_text,
            "new_state": new_state,
            "bot_reply": bot_reply,
            "action_taken": action_taken
        }

    def _handle_random_query(self, query: str) -> str:
        """Handles off-script customer inquiries using NLP intent categorization."""
        q = query.lower()
        if any(w in q for w in ["delivery", "kab", "when", "time", "din", "kitne din", "how many days"]):
            return (
                "Standard delivery takes 3 to 4 business days! 🚚\n\n"
                "To ensure dispatch today, please let us know: Should we confirm your order? (Reply 1 for Yes, 2 for Cancel)."
            )
        elif any(w in q for w in ["address", "change", "badal", "flat", "makan", "pincode"]):
            return (
                "If you need to adjust your address, please reply with your complete updated address right here, "
                "or reply 1 to confirm with current details."
            )
        elif any(w in q for w in ["discount", "offer", "coupon", "kam karo"]):
            return (
                f"We can offer a flat ₹{self.discount_amount:,.0f} OFF if you pay online right now! "
                "Reply 1 to get your discounted payment link."
            )
        else:
            return (
                "Thanks for reaching out! Our team is ready to prepare your parcel. 📦\n\n"
                "Please confirm your order by replying:\n"
                "👉 *1* to Confirm Delivery\n"
                "👉 *2* to Cancel Order"
            )

    def evaluate_timeout(self, hours_elapsed: float) -> dict:
        """Determines automated timeout actions (at 4h, 20h, 24h)."""
        if hours_elapsed < 4:
            return {"status": "ACTIVE_WAITING", "action": "None", "message": None}
        elif 4 <= hours_elapsed < 20:
            return {
                "status": "REMINDER_1_DUE",
                "action": "Send gentle follow-up nudge",
                "message": "Friendly reminder: Please reply 1 to confirm your order so we can dispatch it today! 📦"
            }
        elif 20 <= hours_elapsed < 24:
            return {
                "status": "FINAL_WARNING_DUE",
                "action": "Send final 4-hour cancellation warning",
                "message": "Final call: Unconfirmed COD orders are automatically released in 4 hours to clear warehouse stock."
            }
        else:
            return {
                "status": "EXPIRED_AUTO_HELD",
                "action": "Order automatically held/cancelled",
                "message": "Order expired due to zero customer confirmation after 24 hours. Saved ₹169.40 RTO cost."
            }
