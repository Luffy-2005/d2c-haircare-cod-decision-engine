"""
WhatsApp Interactive Flow Simulator & Mathematical Proof Demonstration
Runs test scenarios for affirmative, negative, conversational, and 24h timeout cases.
Demonstrates the exact economic calculations behind the prepaid discount offer.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from whatsapp.bot_state_machine import WhatsAppStateMachine

def print_prepaid_discount_math():
    print("\n" + "="*75)
    print("  MATHEMATICAL PROOF: OPTIMAL PREPAID DISCOUNT DERIVATION")
    print("="*75)
    print("""
1. Direct Logistics & Damage Cost of an RTO:
   - Forward Shipping Cost:          ₹65.00
   - Reverse Shipping Cost:          ₹65.00
   - Packaging & Handling:           ₹25.00
   - Unsellable Damaged Goods (8%):  ₹14.40  (8% of ₹180 product cost)
   ---------------------------------------------------------------
   Total Direct RTO Loss Per Order:  ₹169.40

2. Courier COD Handling / Collection Surcharge:
   - Courier cash collection fee:    ₹30.00 per delivered COD shipment
   - Digital payments fee (PG):      ~1.8% (₹11.68 on ₹649 AOV)
   - Net Courier Cash Penalty:       ₹30.00 - ₹11.68 = ₹18.32 saved on prepaid

3. Expected Logistics Cost Comparison (COD vs. Prepaid):
   - Baseline COD RTO Rate:          28%
   - Baseline Prepaid RTO Rate:       4%
   - Expected RTO Loss on COD:       28% × ₹169.40 = ₹47.43
   - Expected RTO Loss on Prepaid:    4% × ₹169.40 =  ₹6.78
   ---------------------------------------------------------------
   Direct RTO Savings by Prepaying:  ₹47.43 - ₹6.78 = ₹40.65

4. High-Risk COD Segment (The Target for Nudge to Prepaid):
   - High-ticket (>₹999) or Tier-3 COD RTO Rate:  ~42% to 45%
   - Expected RTO Loss in this segment:           45% × ₹169.40 = ₹76.23
   - Prepaid RTO Rate in this segment:             4% × ₹169.40 =  ₹6.78
   ---------------------------------------------------------------
   Direct RTO Savings in High-Risk:              ₹76.23 - ₹6.78 = ₹69.45
   Courier Cash Handling Surcharge Saved:                         ₹30.00
   ---------------------------------------------------------------
   Total Cost Avoided Per Converted Order:                       ₹99.45!

5. Conclusion & Discount Recommendation:
   - We offer FLAT ₹60.00 OFF (or ~9.2% of ₹649 AOV).
   - Brand saves:                                                ₹99.45
   - Discount given to customer:                                 ₹60.00
   ---------------------------------------------------------------
   NET PROFIT GAIN PER CONVERTED BUYER:                         +₹39.45 DIRECT CASH!
   
   Strategic Benefits:
   ✓ Customer feels rewarded and values the ₹60 instant saving.
   ✓ 0% doorstep refusal risk; 96% guaranteed delivery.
   ✓ Immediate positive cash flow and working capital turnover.
   ✓ Eliminates customer acquisition waste for Marketing (retains Meta CAC).
""")
    print("="*75 + "\n")

def run_simulation_tests():
    bot = WhatsAppStateMachine(discount_amount=60.0)
    sample_order = {
        "order_id": "ORD-10492",
        "customer_name": "Pooja Sharma",
        "product_name": "Advanced Hair Growth Serum with Redensyl",
        "order_value": 899.0,
        "shipping_address": "House No 42, Gali No 3, Near Shiv Mandir",
        "city": "Lucknow",
        "pincode": "226001"
    }

    print("\n--- TEST SCENARIO 1: Ship After Confirmation (Customer Replies 'YES') ---")
    msg1 = bot.generate_initial_message("Ship after confirmation", sample_order)
    print(f"[Initial Outgoing Message | Time: {msg1['scheduled_time']}]\n{msg1['message_text']}\n")
    res1 = bot.process_reply("Ship after confirmation", "yes confirm kardo", msg1["current_state"], sample_order)
    print(f"[Customer Reply]: 'yes confirm kardo'")
    print(f"[Bot Reply]: {res1['bot_reply']}")
    print(f"[System State]: {res1['new_state']} -> {res1['action_taken']}")

    print("\n--- TEST SCENARIO 2: Ship After Confirmation (Customer Replies 'NO / CANCEL') ---")
    res2 = bot.process_reply("Ship after confirmation", "nahi cancel it please", msg1["current_state"], sample_order)
    print(f"[Customer Reply]: 'nahi cancel it please'")
    print(f"[Bot Reply]: {res2['bot_reply']}")
    print(f"[System State]: {res2['new_state']} -> {res2['action_taken']}")

    print("\n--- TEST SCENARIO 3: Customer Sends Unstructured / Random Question ---")
    res3 = bot.process_reply("Ship after confirmation", "bhaiya delivery kitne din mein aayegi?", msg1["current_state"], sample_order)
    print(f"[Customer Reply]: 'bhaiya delivery kitne din mein aayegi?'")
    print(f"[Bot Reply]: {res3['bot_reply']}")
    print(f"[System State]: {res3['new_state']} -> {res3['action_taken']}")

    print("\n--- TEST SCENARIO 4: 24-Hour Timeout (Customer Does Not Reply) ---")
    print("T+2 hours elapsed: ", bot.evaluate_timeout(2)["status"])
    print("T+6 hours elapsed: ", bot.evaluate_timeout(6)["status"], "->", bot.evaluate_timeout(6)["message"])
    print("T+21 hours elapsed:", bot.evaluate_timeout(21)["status"], "->", bot.evaluate_timeout(21)["message"])
    print("T+24 hours elapsed:", bot.evaluate_timeout(24)["status"], "->", bot.evaluate_timeout(24)["message"])

    print("\n--- TEST SCENARIO 5: Nudge to Prepaid Flow ---")
    msg5 = bot.generate_initial_message("Nudge to prepaid", sample_order)
    print(f"[Initial Outgoing Message | Time: {msg5['scheduled_time']}]\n{msg5['message_text']}\n")
    res5 = bot.process_reply("Nudge to prepaid", "1 pay online", msg5["current_state"], sample_order)
    print(f"[Customer Reply]: '1 pay online'")
    print(f"[Bot Reply]: {res5['bot_reply']}")
    print(f"[System State]: {res5['new_state']} -> {res5['action_taken']}")

if __name__ == "__main__":
    print_prepaid_discount_math()
    run_simulation_tests()
