"""
Founder Executive Dashboard & Operations Hub (Flask App)
Answers the morning founder questions:
- How many orders were in each of the 4 buckets yesterday?
- Estimated Rs saved from avoided RTOs
- Estimated Rs lost from cancelled orders that might have been genuine
- Net Rs impact
Includes interactive threshold tuning and WhatsApp simulator.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import yaml
import pandas as pd
from flask import Flask, render_template, request, jsonify
from engine.decision_engine import DecisionEngine
from engine.financial_model import FinancialModel
from whatsapp.bot_state_machine import WhatsAppStateMachine

app = Flask(__name__)

# Initialize singletons
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "orders_sample.csv")
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "rules_config.yaml")

engine = DecisionEngine(config_path=CONFIG_PATH)
state_machine = WhatsAppStateMachine(discount_amount=60.0)

# Load and pre-evaluate dataset
def get_evaluated_data():
    df = pd.read_csv(DATA_PATH)
    return engine.evaluate_dataset(df)

@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/api/stats")
def get_stats():
    timeframe = request.args.get("timeframe", "yesterday")
    evaluated_df = get_evaluated_data()

    # If timeframe is 'yesterday', select the most recent batch of orders (last 100 orders)
    # to simulate a single day's volume (~100 COD orders/day for 3,000 monthly total)
    if timeframe == "yesterday":
        sample_df = evaluated_df.tail(100).copy()
    elif timeframe == "week":
        sample_df = evaluated_df.tail(700).copy()
    else:
        sample_df = evaluated_df.copy()

    fin_model = FinancialModel(engine.config)
    impact = fin_model.calculate_impact(sample_df)

    # Convert recent orders to dict for table display
    table_records = sample_df.tail(30).to_dict(orient="records")

    return jsonify({
        "timeframe": timeframe,
        "impact": impact,
        "recent_orders": table_records,
        "config": engine.config
    })

@app.route("/api/update-config", methods=["POST"])
def update_config():
    new_thresholds = request.json
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        if "cancel_threshold" in new_thresholds:
            cfg["decision_thresholds"]["cancel_risk_score_min"] = int(new_thresholds["cancel_threshold"])
        if "confirm_threshold" in new_thresholds:
            cfg["decision_thresholds"]["confirm_risk_score_min"] = int(new_thresholds["confirm_threshold"])
        if "nudge_threshold" in new_thresholds:
            cfg["decision_thresholds"]["nudge_prepaid_risk_score_min"] = int(new_thresholds["nudge_threshold"])
        if "discount_amount" in new_thresholds:
            cfg["prepaid_nudge_offer"]["discount_amount"] = float(new_thresholds["discount_amount"])
            state_machine.discount_amount = float(new_thresholds["discount_amount"])
        if "min_nudge_value" in new_thresholds:
            cfg["prepaid_nudge_offer"]["min_order_value_to_nudge"] = float(new_thresholds["min_nudge_value"])

        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(cfg, f, default_flow_style=False)

        engine.reload_config()
        return jsonify({"status": "success", "message": "Thresholds updated successfully!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route("/api/evaluate-single", methods=["POST"])
def evaluate_single():
    order_data = request.json
    result = engine.evaluate_order(order_data)
    return jsonify(result)

@app.route("/api/whatsapp/init", methods=["POST"])
def whatsapp_init():
    data = request.json
    flow_type = data.get("flow_type", "Ship after confirmation")
    order = data.get("order", {})
    init_msg = state_machine.generate_initial_message(flow_type, order)
    return jsonify(init_msg)

@app.route("/api/whatsapp/reply", methods=["POST"])
def whatsapp_reply():
    data = request.json
    flow_type = data.get("flow_type", "Ship after confirmation")
    text = data.get("message", "")
    state = data.get("current_state", "WAITING_FOR_REPLY")
    order = data.get("order", {})
    reply_res = state_machine.process_reply(flow_type, text, state, order)
    return jsonify(reply_res)

@app.route("/simulator")
def simulator_page():
    return render_template("simulator.html")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
