# AI USAGE & CORRECTION LOG

This log details the AI tools utilized throughout system development, the exact tasks they accelerated, and specific examples where AI-generated suggestions were flawed, inaccurate, or suboptimal, along with how we identified and corrected them.

---

### 1. SUMMARY OF AI TOOLS UTILIZED

| Tool | Purpose in Workflow |
| :--- | :--- |
| **Claude / Anthropic Models** | Rapid drafting of boilerplate regex patterns, HTML/CSS dashboard layouts, and initial scenario mocks. |
| **Google Gemini (Antigravity Environment)** | Exploratory data analysis, mathematical verification of unit economics, script automation, and test writing. |
| **GitHub Copilot / Code Assistants** | Tab completion for Python type hints, pandas aggregations, and unittest assertions. |

---

### 2. SPECIFIC EXAMPLES WHERE AI WAS WRONG OR WEAK (AND HOW WE FIXED IT)

#### Example 1: Naive Address Completeness Heuristics (Penalizing Vernacular Indian Addresses)
* **What the AI Generated:** When prompted to write an address evaluation function, the AI generated a standard regex that searched strictly for Western address tokens:
  ```python
  # AI'S ORIGINAL NAIVE CODE:
  def is_complete_address(addr):
      return bool(re.search(r'\b(street|road|avenue|blvd|lane|drive|suite|apt)\b', addr.lower()))
  ```
* **Why It Was Flawed:** This regex immediately classified authentic Indian addresses like `"Makan no 14, shiv mandir ke piche wali gali, railway fatak ke samne, purani basti"` as `INCOMPLETE` / `GIBBERISH` because it lacks words like "Avenue" or "Drive"! In our historical dataset, this flawed logic would have mistakenly cancelled over 541 genuine Tier-2 and Tier-3 customers—wasting over ₹1,62,000 in Meta ads acquisition cost.
* **How We Caught & Fixed It:** We inspected the failure modes on the 2,000 orders dataset and observed that colloquial Hindi/Hinglish addresses achieve a high **78.2% delivery success rate**. We replaced the naive Western token matcher with a bilingual Indian postal NLP parser that recognizes navigational landmarks (`"ke piche"`, `"ke samne"`, `"ke paas"`, `"fatak"`, `"makan no"`, `"ward"`, `"basti"`).

---

#### Example 2: Flawed Financial P&L Metric Formulation (Double-Counting CAC and Gross Margins)
* **What the AI Generated:** In early financial impact calculations, the AI proposed this equation for net impact on cancelled orders:
  ```python
  # AI'S ORIGINAL PROPOSAL:
  net_saved = (actual_rtos * 169.40) - (mistaken_cancels * (649.0 + 300.0 + 402.38))
  ```
* **Why It Was Flawed:** The AI was double-counting top-line order revenue (₹649) alongside gross margin (₹402.38) and customer acquisition cost (₹300). Revenue is not profit; gross margin already accounts for COGS. Furthermore, Meta ads CAC (₹300) was already spent when the user clicked the ad and placed the order; cancelling the order does not retroactively charge an additional ₹300 cash, but rather loses the opportunity to amortize that already-spent CAC against the gross profit margin.
* **How We Caught & Fixed It:** We conducted a rigorous unit economic balance sheet review:
  * For an order successfully delivered: Net Cash Contribution = Gross Margin (62% of ₹649 = ₹402.38).
  * For an avoided RTO: Direct Logistics & Damage Cash Saved = ₹169.40.
  * For a mistakenly cancelled order: The lost cash contribution is strictly the Gross Margin (₹402.38).
  * We corrected the formula in `engine/financial_model.py` to reflect true bottom-line EBITDA impact.

---

#### Example 3: Brittle WhatsApp Chat State Transitions (Keyword Exact Match Failure)
* **What the AI Generated:** When constructing the state machine for the WhatsApp confirmation flow, the AI used rigid exact string matching:
  ```python
  # AI'S ORIGINAL STATE HANDLER:
  if text in ["yes", "1", "confirm"]:
      state = "CONFIRMED"
  elif text in ["no", "2", "cancel"]:
      state = "CANCELLED"
  ```
* **Why It Was Flawed:** Real Indian consumers rarely text isolated single words. In practice, customers respond with mixed conversational Hindi/English phrases like:
  * *"1 pay online please link bhejo"*
  * *"haan bhaiya bhej do"*
  * *"nahi cancel kardo man badal gaya"*
  Under the AI's exact-match logic, every single one of these natural replies triggered the unhelpful fallback message: *"Invalid input, please type 1 or 2"*, causing high customer frustration and abandonment.
* **How We Caught & Fixed It:** We wrote comprehensive unit tests simulating real conversational replies. When test cases failed, we upgraded the state machine to use flexible token boundary matching, multi-word intent parsing, and natural language query fallbacks that answer delivery timeline questions before re-prompting.
