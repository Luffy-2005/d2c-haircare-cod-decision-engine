"""
Unit & Integration Tests for COD Decision Engine & WhatsApp Flows
"""

import unittest
import pandas as pd
from engine.address_analyzer import AddressAnalyzer
from engine.fraud_detector import FraudDetector
from engine.decision_engine import DecisionEngine
from engine.financial_model import FinancialModel
from whatsapp.bot_state_machine import WhatsAppStateMachine

class TestDecisionEngine(unittest.TestCase):
    def setUp(self):
        self.engine = DecisionEngine("config/rules_config.yaml")
        self.address_analyzer = AddressAnalyzer()
        self.fraud_detector = FraudDetector()
        self.bot = WhatsAppStateMachine(discount_amount=60.0)

    def test_fake_name_detection(self):
        eval_asdf = self.address_analyzer.evaluate("asdf", "Flat 201, Sunshine Apts, MG Road")
        self.assertTrue(eval_asdf["is_fake_name"])
        self.assertIn("recognized test/placeholder", eval_asdf["name_reason"])

        eval_real = self.address_analyzer.evaluate("Pooja Sharma", "Flat 201, Sunshine Apts, MG Road")
        self.assertFalse(eval_real["is_fake_name"])

    def test_hinglish_vs_vague_address(self):
        # Authentic Hinglish address
        hinglish_addr = "Makan no 14, shiv mandir ke piche wali gali, railway fatak ke samne, purani basti"
        eval_h = self.address_analyzer.evaluate("Rahul Kumar", hinglish_addr)
        self.assertEqual(eval_h["address_category"], "HINGLISH_VALID")
        self.assertTrue(eval_h["doorstep_deliverable"])

        # Vague address
        vague_addr = "Near bus stand"
        eval_v = self.address_analyzer.evaluate("Rahul Kumar", vague_addr)
        self.assertEqual(eval_v["address_category"], "VAGUE")
        self.assertFalse(eval_v["doorstep_deliverable"])

    def test_phone_validation(self):
        self.assertTrue(self.fraud_detector.validate_phone("9823012345")["is_valid"])
        self.assertFalse(self.fraud_detector.validate_phone("9999999999")["is_valid"])
        self.assertFalse(self.fraud_detector.validate_phone("9876543210")["is_valid"])
        self.assertFalse(self.fraud_detector.validate_phone("12345")["is_valid"])

    def test_hold_cancel_on_fraud(self):
        order = {
            "order_id": "ORD-TEST-1",
            "customer_name": "asdf",
            "shipping_address": "test address 123",
            "customer_phone": "9999999999",
            "pincode": "999999",
            "order_value": 499.0,
            "past_orders_count": 0,
            "past_rto_count": 0
        }
        res = self.engine.evaluate_order(order)
        self.assertEqual(res["action"], "Hold / cancel")
        self.assertIn("Cancelled/Held", res["plain_english_reason"])

    def test_ship_as_is_for_trusted_repeat(self):
        order = {
            "order_id": "ORD-TEST-2",
            "customer_name": "Aarav Sharma",
            "shipping_address": "Flat 402, Lotus Residency, Near HDFC Bank, Kothrud, Pune",
            "customer_phone": "9823012345",
            "pincode": "411038",
            "order_value": 649.0,
            "past_orders_count": 3,
            "past_rto_count": 0
        }
        res = self.engine.evaluate_order(order)
        self.assertEqual(res["action"], "Ship as-is")
        self.assertLessEqual(res["risk_score"], 39)

    def test_nudge_to_prepaid_for_high_value(self):
        order = {
            "order_id": "ORD-TEST-3",
            "customer_name": "Deepak Patel",
            "shipping_address": "House No 12, Street 4, Behind Civil Hospital",
            "customer_phone": "9879012345",
            "pincode": "800001",
            "order_value": 1299.0,
            "past_orders_count": 0,
            "past_rto_count": 0
        }
        res = self.engine.evaluate_order(order)
        self.assertEqual(res["action"], "Nudge to prepaid")
        self.assertIn("Nudge to Prepaid", res["plain_english_reason"])

    def test_whatsapp_state_machine_replies(self):
        sample_order = {"order_id": "ORD-1", "customer_name": "Test", "order_value": 649.0}
        
        # Confirmation Yes
        reply_yes = self.bot.process_reply("Ship after confirmation", "yes", "WAITING", sample_order)
        self.assertEqual(reply_yes["new_state"], "CONFIRMED_FOR_DISPATCH")

        # Confirmation No
        reply_no = self.bot.process_reply("Ship after confirmation", "cancel it", "WAITING", sample_order)
        self.assertEqual(reply_no["new_state"], "CANCELLED_BY_CUSTOMER")

        # Prepaid Link
        reply_pay = self.bot.process_reply("Nudge to prepaid", "1 pay online", "WAITING", sample_order)
        self.assertEqual(reply_pay["new_state"], "PREPAID_LINK_SENT")

        # Timeout
        t24 = self.bot.evaluate_timeout(24)
        self.assertEqual(t24["status"], "EXPIRED_AUTO_HELD")

if __name__ == "__main__":
    unittest.main()
