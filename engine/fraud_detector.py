"""
Algorithmic Fraud & Heuristics Detector
Handles high-speed mathematical & logical checks where LLMs should NOT be used:
- Regex phone number validation
- 6-digit Pincode sanity & regional delivery reliability lookup
- Historical order & RTO frequency calculation
"""

import re

class FraudDetector:
    def __init__(self, high_rto_pincodes=None):
        # High RTO postal zones identified from historical courier partner logs (Tier 3/remote)
        self.high_rto_pincodes = high_rto_pincodes or {
            "800001", "800020", "800026", "834001", "834005", "221001", "221005",
            "823001", "842001", "842002", "846004", "250001", "250002", "202001"
        }
        self.invalid_pincodes = {"000000", "999999", "123456", "111111", "123123"}

    def validate_phone(self, phone: str) -> dict:
        """Sanity check for 10-digit Indian mobile number."""
        digits = re.sub(r'\D', '', str(phone or ''))
        # Standard Indian mobile numbers are 10 digits starting with 6, 7, 8, or 9
        if len(digits) == 12 and digits.startswith("91"):
            digits = digits[2:]
        elif len(digits) == 11 and digits.startswith("0"):
            digits = digits[1:]

        if len(digits) != 10:
            return {
                "is_valid": False,
                "reason": f"Phone number has invalid length ({len(digits)} digits instead of 10)."
            }

        if not digits[0] in "6789":
            return {
                "is_valid": False,
                "reason": f"Phone number begins with invalid digit '{digits[0]}'. Must start with 6, 7, 8, or 9."
            }

        # Check for repetitive sequences (e.g. 9999999999, 1234567890)
        if len(set(digits)) <= 2:
            return {
                "is_valid": False,
                "reason": "Phone number contains suspicious repetitive digits."
            }
        if digits in ["1234567890", "9876543210"]:
            return {
                "is_valid": False,
                "reason": "Phone number matches obvious sequential dummy sequence."
            }

        return {"is_valid": True, "reason": "Valid 10-digit Indian mobile number."}

    def evaluate_pincode(self, pincode: str) -> dict:
        """Evaluates 6-digit postal code deliverability & zone risk."""
        pin_str = str(pincode or '').strip()

        if not (pin_str.isdigit() and len(pin_str) == 6):
            return {
                "is_valid": False,
                "is_high_risk": True,
                "reason": f"Pincode '{pin_str}' is malformed (must be exactly 6 digits)."
            }

        if pin_str in self.invalid_pincodes:
            return {
                "is_valid": False,
                "is_high_risk": True,
                "reason": f"Pincode '{pin_str}' is a dummy/non-existent postal code."
            }

        if pin_str in self.high_rto_pincodes:
            return {
                "is_valid": True,
                "is_high_risk": True,
                "reason": f"Pincode '{pin_str}' is in a historically high RTO remote postal zone."
            }

        return {
            "is_valid": True,
            "is_high_risk": False,
            "reason": f"Pincode '{pin_str}' is serviceable with standard delivery SLA."
        }

    def evaluate_customer_history(self, past_orders: int, past_rto: int) -> dict:
        """Evaluates past buyer track record."""
        past_orders = int(past_orders or 0)
        past_rto = int(past_rto or 0)

        if past_orders == 0:
            return {
                "is_repeat": False,
                "is_chronic_rto": False,
                "is_trusted_buyer": False,
                "rto_ratio": 0.0,
                "reason": "First-time buyer (acquired via Meta ads, no past order history)."
            }

        rto_ratio = past_rto / past_orders if past_orders > 0 else 0.0

        if past_rto >= 2 and rto_ratio >= 0.50:
            return {
                "is_repeat": True,
                "is_chronic_rto": True,
                "is_trusted_buyer": False,
                "rto_ratio": rto_ratio,
                "reason": f"Chronic RTO customer ({past_rto} out of {past_orders} past orders returned)."
            }

        if past_orders >= 1 and past_rto == 0:
            return {
                "is_repeat": True,
                "is_chronic_rto": False,
                "is_trusted_buyer": True,
                "rto_ratio": 0.0,
                "reason": f"Verified loyal customer ({past_orders} past deliveries, 0 returns)."
            }

        return {
            "is_repeat": True,
            "is_chronic_rto": False,
            "is_trusted_buyer": False,
            "rto_ratio": rto_ratio,
            "reason": f"Repeat customer with mixed history ({past_rto}/{past_orders} past RTOs)."
        }
