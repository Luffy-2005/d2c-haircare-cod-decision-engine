"""
Unified COD Decision Engine
Orchestrates LLM address/identity analysis and algorithmic fraud detection
to output one of four business actions with plain-English reasoning:
1. Ship as-is
2. Ship after confirmation
3. Nudge to prepaid
4. Hold / cancel
"""

import os
import yaml
import pandas as pd
from engine.address_analyzer import AddressAnalyzer
from engine.fraud_detector import FraudDetector

class DecisionEngine:
    def __init__(self, config_path="config/rules_config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.address_analyzer = AddressAnalyzer()
        self.fraud_detector = FraudDetector()

    def _load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {}

    def reload_config(self):
        self.config = self._load_config()

    def evaluate_order(self, order: dict) -> dict:
        """
        Evaluates a single COD order and returns:
        - action: "Ship as-is" | "Ship after confirmation" | "Nudge to prepaid" | "Hold / cancel"
        - risk_score: int (0 - 100)
        - plain_english_reason: str
        - details: dict of feature breakdown
        """
        thresholds = self.config.get("decision_thresholds", {})
        weights = self.config.get("risk_scoring_weights", {})
        prepaid_cfg = self.config.get("prepaid_nudge_offer", {})

        customer_name = str(order.get("customer_name", ""))
        shipping_address = str(order.get("shipping_address", ""))
        customer_phone = str(order.get("customer_phone", ""))
        pincode = str(order.get("pincode", ""))
        order_value = float(order.get("order_value", 0))
        past_orders = int(order.get("past_orders_count", 0))
        past_rto = int(order.get("past_rto_count", 0))

        # 1. LLM / NLP Address & Identity Evaluation
        address_eval = self.address_analyzer.evaluate(customer_name, shipping_address)

        # 2. Heuristic & Algorithmic Evaluation
        phone_eval = self.fraud_detector.validate_phone(customer_phone)
        pincode_eval = self.fraud_detector.evaluate_pincode(pincode)
        history_eval = self.fraud_detector.evaluate_customer_history(past_orders, past_rto)

        # 3. Compute Composite Risk Score (0 - 100)
        risk_score = 20  # Baseline COD risk in India (~20-25%)
        reasons = []

        # Name checks
        if address_eval["is_fake_name"]:
            risk_score += weights.get("fake_name_penalty", 50)
            reasons.append(address_eval["name_reason"])

        # Address quality
        addr_cat = address_eval["address_category"]
        if addr_cat == "GIBBERISH":
            risk_score += weights.get("address_gibberish_penalty", 50)
            reasons.append("Address is gibberish/test text.")
        elif addr_cat == "VAGUE":
            risk_score += weights.get("address_vague_penalty", 35)
            reasons.append("Address is incomplete (lacks house/street details).")
        elif addr_cat == "HINGLISH_VALID":
            risk_score += weights.get("address_hinglish_friction", 12)
            reasons.append("Colloquial Hinglish address with local landmarks.")
        elif addr_cat == "COMPLETE":
            risk_score += weights.get("address_complete_bonus", -15)

        # Phone validity
        if not phone_eval["is_valid"]:
            risk_score += weights.get("invalid_phone_penalty", 45)
            reasons.append(phone_eval["reason"])

        # Pincode deliverability
        if not pincode_eval["is_valid"]:
            risk_score += 45
            reasons.append(pincode_eval["reason"])
        elif pincode_eval["is_high_risk"]:
            risk_score += weights.get("remote_tier3_pincode_penalty", 20)
            reasons.append("Remote pincode with elevated return rates.")

        # History
        if history_eval["is_chronic_rto"]:
            risk_score += weights.get("chronic_rto_penalty", 45)
            reasons.append(history_eval["reason"])
        elif history_eval["is_trusted_buyer"]:
            risk_score += weights.get("repeat_clean_bonus", -25)
        elif not history_eval["is_repeat"]:
            risk_score += weights.get("first_time_buyer_penalty", 10)

        # High Order Value
        if order_value >= 1000:
            risk_score += weights.get("high_ticket_penalty", 15)
            reasons.append(f"High COD order value (Rs. {order_value:,.0f}).")

        # Clamp risk score to [0, 100]
        risk_score = max(0, min(100, risk_score))

        # 4. Action Decision Logic
        cancel_thresh = thresholds.get("cancel_risk_score_min", 80)
        nudge_thresh = thresholds.get("nudge_prepaid_risk_score_min", 45)
        confirm_thresh = thresholds.get("confirm_risk_score_min", 40)
        min_nudge_val = prepaid_cfg.get("min_order_value_to_nudge", 799.0)
        discount_amt = prepaid_cfg.get("discount_amount", 60.0)

        # Check for hard Hold/Cancel triggers
        hard_cancel = (
            address_eval["is_fake_name"] or
            addr_cat == "GIBBERISH" or
            not phone_eval["is_valid"] or
            not pincode_eval["is_valid"] or
            history_eval["is_chronic_rto"] or
            risk_score >= cancel_thresh
        )

        if hard_cancel:
            action = "Hold / cancel"
            primary_reason = reasons[0] if reasons else "Extreme risk score exceeding cancel threshold."
            plain_english_reason = f"Cancelled/Held: {primary_reason} Prevents Rs. 169.40 direct logistics burn."

        elif (order_value >= min_nudge_val and risk_score >= nudge_thresh) or \
             (pincode_eval["is_high_risk"] and order_value >= 600):
            action = "Nudge to prepaid"
            reason_text = "High-ticket COD order" if order_value >= min_nudge_val else "Remote delivery zone"
            plain_english_reason = (
                f"Nudge to Prepaid: {reason_text} with moderate risk ({risk_score}/100). "
                f"Offer Rs. {discount_amt:.0f} discount on WhatsApp to convert online and cut RTO from 28% to 4%."
            )

        elif risk_score >= confirm_thresh:
            action = "Ship after confirmation"
            summary_cause = reasons[0] if reasons else "First-time buyer with unverified details"
            plain_english_reason = (
                f"Ship after Confirmation: {summary_cause} (Risk score: {risk_score}/100). "
                f"Requires customer WhatsApp verification before dispatch."
            )

        else:
            action = "Ship as-is"
            trust_factor = "Verified repeat customer" if history_eval["is_trusted_buyer"] else "Complete address and valid contact"
            plain_english_reason = (
                f"Ship Immediately: Low risk score ({risk_score}/100). {trust_factor} in serviceable pincode."
            )

        return {
            "order_id": order.get("order_id", ""),
            "action": action,
            "risk_score": risk_score,
            "plain_english_reason": plain_english_reason,
            "address_eval": address_eval,
            "phone_eval": phone_eval,
            "pincode_eval": pincode_eval,
            "history_eval": history_eval
        }

    def evaluate_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        """Evaluates an entire DataFrame of orders and appends decision columns."""
        results = []
        for _, row in df.iterrows():
            eval_res = self.evaluate_order(row.to_dict())
            results.append({
                "decision_action": eval_res["action"],
                "risk_score": eval_res["risk_score"],
                "decision_reason": eval_res["plain_english_reason"]
            })
        results_df = pd.DataFrame(results)
        return pd.concat([df.reset_index(drop=True), results_df], axis=1)
