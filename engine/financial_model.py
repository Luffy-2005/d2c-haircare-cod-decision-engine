"""
Financial Modeling & P&L Impact Accounting
Strict INR (Rs.) calculations balancing Operations logistics cost savings
against Marketing customer acquisition & gross margin retention.
"""

class FinancialModel:
    def __init__(self, config: dict):
        fin = config.get("financial_parameters", {})
        prepaid = config.get("prepaid_nudge_offer", {})

        self.forward_shipping = fin.get("forward_shipping_cost", 65.0)
        self.return_shipping = fin.get("return_shipping_cost", 65.0)
        self.packaging_handling = fin.get("packaging_handling_cost", 25.0)
        self.damage_rate = fin.get("damaged_return_rate", 0.08)
        self.product_cost = fin.get("average_product_cost", 180.0)
        
        # Rs. 169.40 total direct cost per RTO
        self.rto_cost_per_order = (
            self.forward_shipping +
            self.return_shipping +
            self.packaging_handling +
            (self.damage_rate * self.product_cost)
        )
        
        self.aov = fin.get("average_order_value", 649.0)
        self.gross_margin = fin.get("gross_margin_rate", 0.62)
        self.gross_profit_per_order = self.aov * self.gross_margin  # Rs. 402.38
        self.cac = fin.get("cac_meta_ads", 300.0)
        self.prepaid_rto_rate = fin.get("prepaid_baseline_rto_rate", 0.04)
        self.cod_courier_fee = fin.get("cod_courier_collection_fee", 30.0)
        
        self.discount_amount = prepaid.get("discount_amount", 60.0)

    def calculate_impact(self, evaluated_df) -> dict:
        """
        Calculates executive metrics from an evaluated dataset:
        - Bucket distributions
        - Estimated Rs saved from avoided RTOs
        - Estimated Rs lost from cancelled genuine orders
        - Net Rs impact
        """
        total_orders = len(evaluated_df)
        if total_orders == 0:
            return {}

        counts = evaluated_df["decision_action"].value_counts().to_dict()
        ship_as_is = counts.get("Ship as-is", 0)
        ship_confirm = counts.get("Ship after confirmation", 0)
        nudge_prepaid = counts.get("Nudge to prepaid", 0)
        hold_cancel = counts.get("Hold / cancel", 0)

        # 1. Hold / cancel bucket
        # In our dataset, identify actual ground truth delivery_status for cancelled orders
        cancelled_rows = evaluated_df[evaluated_df["decision_action"] == "Hold / cancel"]
        actual_rtos_cancelled = (cancelled_rows["delivery_status"] == "RTO").sum() if "delivery_status" in cancelled_rows else int(hold_cancel * 0.95)
        actual_delivered_cancelled = (cancelled_rows["delivery_status"] == "Delivered").sum() if "delivery_status" in cancelled_rows else int(hold_cancel * 0.05)

        # Money saved by not shipping orders that would have returned
        savings_from_cancel = actual_rtos_cancelled * self.rto_cost_per_order
        
        # Money lost from genuine customers cancelled (lost gross margin)
        # Note: Meta CAC was already spent at ad click; the lost opportunity is gross margin
        loss_from_cancel = actual_delivered_cancelled * self.gross_profit_per_order

        # 2. Ship after confirmation bucket
        # WhatsApp confirmation filter: ~82% confirm (intent reaffirmed, RTO drops to 8%), ~18% fail to confirm / cancel
        # The 18% who don't confirm are held, saving RTO on uncommitted impulse shoppers (~65% would have RTO'd)
        unconfirmed_held = int(ship_confirm * 0.18)
        avoided_rto_unconfirmed = unconfirmed_held * 0.65
        
        # The 82% confirmed see their delivery rate rise from baseline 72% to 92% (20 percentage points RTO drop)
        confirmed_shipped = ship_confirm - unconfirmed_held
        avoided_rto_confirmed = confirmed_shipped * 0.20
        
        savings_from_confirm = (avoided_rto_unconfirmed + avoided_rto_confirmed) * self.rto_cost_per_order

        # 3. Nudge to prepaid bucket
        # ~28% of customers accept prepaid nudge for Rs. 60 off
        converted_prepaid = int(nudge_prepaid * 0.28)
        # For converted orders: RTO drops from ~35% (high-ticket/remote COD) to 4% (prepaid baseline)
        avoided_rto_prepaid = converted_prepaid * (0.35 - self.prepaid_rto_rate)
        savings_from_prepaid_rto = avoided_rto_prepaid * self.rto_cost_per_order
        savings_from_cod_courier_fee = converted_prepaid * self.cod_courier_fee
        total_prepaid_savings = savings_from_prepaid_rto + savings_from_cod_courier_fee
        
        # Cost of discounts provided
        cost_of_discounts = converted_prepaid * self.discount_amount

        # 4. Aggregations
        total_saved = savings_from_cancel + savings_from_confirm + total_prepaid_savings
        total_lost = loss_from_cancel + cost_of_discounts
        net_impact = total_saved - total_lost

        return {
            "total_orders": total_orders,
            "buckets": {
                "ship_as_is": {"count": ship_as_is, "pct": round(ship_as_is / total_orders * 100, 1)},
                "ship_after_confirmation": {"count": ship_confirm, "pct": round(ship_confirm / total_orders * 100, 1)},
                "nudge_to_prepaid": {"count": nudge_prepaid, "pct": round(nudge_prepaid / total_orders * 100, 1)},
                "hold_cancel": {"count": hold_cancel, "pct": round(hold_cancel / total_orders * 100, 1)},
            },
            "financials": {
                "total_saved_from_avoided_rtos": round(total_saved, 2),
                "total_lost_from_genuine_cancellations": round(loss_from_cancel, 2),
                "discounts_given": round(cost_of_discounts, 2),
                "net_impact_inr": round(net_impact, 2),
                "rto_cost_unit": round(self.rto_cost_per_order, 2),
                "gross_margin_unit": round(self.gross_profit_per_order, 2)
            },
            "breakdown": {
                "cancel_avoided_rtos": int(actual_rtos_cancelled),
                "cancel_mistaken_cancellations": int(actual_delivered_cancelled),
                "confirm_avoided_rtos": round(avoided_rto_unconfirmed + avoided_rto_confirmed, 1),
                "prepaid_converted_orders": converted_prepaid
            }
        }
