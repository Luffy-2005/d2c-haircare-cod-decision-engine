// Executive Dashboard Controller

let currentStats = null;

async function loadDashboardStats() {
  const timeframe = document.getElementById("timeframeSelect").value;
  try {
    const res = await fetch(`/api/stats?timeframe=${timeframe}`);
    const data = await res.json();
    currentStats = data;
    renderDashboard(data);
  } catch (err) {
    console.error("Failed to load dashboard stats:", err);
  }
}

function renderDashboard(data) {
  const impact = data.impact || {};
  const fin = impact.financials || {};
  const buckets = impact.buckets || {};

  // 1. Financial KPIs
  document.getElementById("savedVal").innerText = `₹${(fin.total_saved_from_avoided_rtos || 0).toLocaleString("en-IN")}`;
  document.getElementById("lostVal").innerText = `₹${(fin.total_lost_from_genuine_cancellations || 0).toLocaleString("en-IN")}`;
  document.getElementById("discountVal").innerText = `₹${(fin.discounts_given || 0).toLocaleString("en-IN")}`;
  
  const netImpact = fin.net_impact_inr || 0;
  const netElem = document.getElementById("netVal");
  netElem.innerText = `${netImpact >= 0 ? "+" : ""}₹${netImpact.toLocaleString("en-IN")}`;
  netElem.className = `kpi-value ${netImpact >= 0 ? "green" : "red"}`;

  // 2. Buckets Distribution
  const bShipAsIs = buckets.ship_as_is || { count: 0, pct: 0 };
  const bConfirm = buckets.ship_after_confirmation || { count: 0, pct: 0 };
  const bNudge = buckets.nudge_to_prepaid || { count: 0, pct: 0 };
  const bCancel = buckets.hold_cancel || { count: 0, pct: 0 };

  document.getElementById("countShipAsIs").innerText = bShipAsIs.count;
  document.getElementById("pctShipAsIs").innerText = `${bShipAsIs.pct}% of volume`;
  document.getElementById("barShipAsIs").style.width = `${bShipAsIs.pct}%`;

  document.getElementById("countConfirm").innerText = bConfirm.count;
  document.getElementById("pctConfirm").innerText = `${bConfirm.pct}% of volume`;
  document.getElementById("barConfirm").style.width = `${bConfirm.pct}%`;

  document.getElementById("countNudge").innerText = bNudge.count;
  document.getElementById("pctNudge").innerText = `${bNudge.pct}% of volume`;
  document.getElementById("barNudge").style.width = `${bNudge.pct}%`;

  document.getElementById("countCancel").innerText = bCancel.count;
  document.getElementById("pctCancel").innerText = `${bCancel.pct}% of volume`;
  document.getElementById("barCancel").style.width = `${bCancel.pct}%`;

  // 3. Orders Table
  renderOrdersTable(data.recent_orders || []);

  // 4. Update Modal Inputs
  const cfg = data.config || {};
  const dt = cfg.decision_thresholds || {};
  const pn = cfg.prepaid_nudge_offer || {};
  if (document.getElementById("inputCancelThresh")) {
    document.getElementById("inputCancelThresh").value = dt.cancel_risk_score_min || 80;
    document.getElementById("inputConfirmThresh").value = dt.confirm_risk_score_min || 40;
    document.getElementById("inputMinNudgeVal").value = pn.min_order_value_to_nudge || 799;
    document.getElementById("inputDiscountAmt").value = pn.discount_amount || 60;
  }
}

function renderOrdersTable(orders) {
  const tbody = document.getElementById("ordersBody");
  tbody.innerHTML = "";

  orders.forEach(order => {
    const tr = document.createElement("tr");

    let badgeClass = "badge-ship-as-is";
    if (order.decision_action === "Ship after confirmation") badgeClass = "badge-confirm";
    if (order.decision_action === "Nudge to prepaid") badgeClass = "badge-nudge";
    if (order.decision_action === "Hold / cancel") badgeClass = "badge-cancel";

    const riskColor = order.risk_score >= 75 ? "#ef4444" : order.risk_score >= 40 ? "#f59e0b" : "#10b981";

    tr.innerHTML = `
      <td><strong>${order.order_id}</strong></td>
      <td>
        <div>${order.customer_name}</div>
        <div style="font-size:11px; color:#94a3b8;">${order.customer_phone || ''}</div>
      </td>
      <td style="max-width:280px;">
        <div style="font-size:12px;">${order.shipping_address}</div>
        <div style="font-size:11px; color:#94a3b8;">${order.city}, ${order.state} - <strong>${order.pincode}</strong></div>
      </td>
      <td><strong>₹${Number(order.order_value).toLocaleString("en-IN")}</strong></td>
      <td>
        <span class="risk-pill" style="color:${riskColor};">${order.risk_score}/100</span>
      </td>
      <td>
        <span class="badge ${badgeClass}">${order.decision_action}</span>
      </td>
      <td style="max-width:320px; font-size:12px; color:#cbd5e1;">
        ${order.decision_reason}
      </td>
      <td>
        ${order.decision_action === "Ship after confirmation" || order.decision_action === "Nudge to prepaid"
          ? `<a href="/simulator" target="_blank" style="color:#3b82f6; text-decoration:none; font-weight:600; font-size:12px;">Test Flow →</a>`
          : `<span style="color:#64748b; font-size:11px;">N/A</span>`
        }
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function filterOrdersTable() {
  const query = document.getElementById("orderSearch").value.toLowerCase();
  const rows = document.querySelectorAll("#ordersBody tr");

  rows.forEach(row => {
    const text = row.innerText.toLowerCase();
    row.style.display = text.includes(query) ? "" : "none";
  });
}

function openThresholdModal() {
  document.getElementById("thresholdModal").style.display = "flex";
}

function closeThresholdModal() {
  document.getElementById("thresholdModal").style.display = "none";
}

async function saveThresholds() {
  const cancelThresh = document.getElementById("inputCancelThresh").value;
  const confirmThresh = document.getElementById("inputConfirmThresh").value;
  const minNudgeVal = document.getElementById("inputMinNudgeVal").value;
  const discountAmt = document.getElementById("inputDiscountAmt").value;

  try {
    const res = await fetch("/api/update-config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        cancel_threshold: cancelThresh,
        confirm_threshold: confirmThresh,
        min_nudge_value: minNudgeVal,
        discount_amount: discountAmt
      })
    });
    const result = await res.json();
    if (result.status === "success") {
      closeThresholdModal();
      loadDashboardStats();
    } else {
      alert("Error: " + result.message);
    }
  } catch (err) {
    alert("Failed to update thresholds: " + err);
  }
}

window.onload = () => {
  loadDashboardStats();
};
