"""
Unified CLI & Application Runner
D2C Haircare COD Decision Engine & Executive Dashboard
"""

import sys
import os
import argparse

# Ensure local imports work reliably
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description="D2C Haircare COD AI Decision System")
    parser.add_argument("--test", action="store_true", help="Run automated unit test suite")
    parser.add_argument("--simulate", action="store_true", help="Run WhatsApp chat simulator & discount math proof")
    parser.add_argument("--eval", action="store_true", help="Run full batch evaluation on orders_sample.csv")
    parser.add_argument("--port", type=int, default=5000, help="Web dashboard port (default: 5000)")
    args = parser.parse_args()

    if args.test:
        import unittest
        loader = unittest.TestLoader()
        suite = loader.discover("tests")
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        sys.exit(0 if result.wasSuccessful() else 1)

    elif args.simulate:
        from whatsapp.simulator import print_prepaid_discount_math, run_simulation_tests
        print_prepaid_discount_math()
        run_simulation_tests()

    elif args.eval:
        import pandas as pd
        from engine.decision_engine import DecisionEngine
        from engine.financial_model import FinancialModel

        csv_path = os.path.join(os.path.dirname(__file__), "data", "orders_sample.csv")
        if not os.path.exists(csv_path):
            from data.generate_dataset import generate_orders_dataset
            generate_orders_dataset(csv_path)

        df = pd.read_csv(csv_path)
        engine = DecisionEngine()
        evaluated_df = engine.evaluate_dataset(df)

        fin = FinancialModel(engine.config)
        impact = fin.calculate_impact(evaluated_df)

        print("\n" + "="*70)
        print("   EXECUTIVE COD PERFORMANCE EVALUATION (2,000 ORDERS)")
        print("="*70)
        print(f"Total Orders Evaluated: {impact['total_orders']:,}")
        print("\n[Bucket Allocation]:")
        for bucket, data in impact["buckets"].items():
            print(f"  • {bucket.replace('_', ' ').title():<28}: {data['count']:>5} orders ({data['pct']}%)")

        print("\n[Financial Impact (INR)]:")
        f = impact["financials"]
        print(f"  • Estimated Rs. Saved (Avoided RTOs):      +Rs. {f['total_saved_from_avoided_rtos']:>10,.2f}")
        print(f"  • Estimated Rs. Lost (Genuine Orders Held): -Rs. {f['total_lost_from_genuine_cancellations']:>10,.2f}")
        print(f"  • Prepaid Discounts Given (Rs. 60 Offer):   -Rs. {f['discounts_given']:>10,.2f}")
        print(f"  -------------------------------------------------------------")
        print(f"  • NET PROFIT IMPACT:                       +Rs. {f['net_impact_inr']:>10,.2f}")
        print("="*70 + "\n")

    else:
        from web.app import app
        print("\n" + "="*70)
        print("  Starting D2C Haircare COD Executive Dashboard & Simulator")
        print(f"  URL: http://127.0.0.1:{args.port}/")
        print("  WhatsApp Simulator: http://127.0.0.1:5000/simulator")
        print("="*70 + "\n")
        app.run(host="127.0.0.1", port=args.port, debug=False)

if __name__ == "__main__":
    main()
