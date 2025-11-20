"""
Satirical CO2 Emission Calculator (Streamlit)

Single-file Streamlit app. Enter purchase details and get:
 - estimated CO2e for the purchase
 - a short sarcastic feedback message (unique/varied)
 - a sustainability tip (varies each time and is context-aware)
 - comparisons (car km, tree-years, smartphone-charges)

To run:
 1. pip install streamlit
 2. streamlit run satirical_co2_calculator.py

Notes:
 - Emission factors are improved and made more category-aware (still simplified).
 - Tips are now templated and conditioned on category, shipping mode, and weight to
   give more relevant and varied suggestions while keeping the satirical tone.
 - This remains a single Python/Streamlit app (no external services required).

This is intentionally humorous; numbers are estimations for demonstration only.
"""

import streamlit as st
from datetime import datetime
import random
import math
import hashlib

# --------------------------
# Improved emission factors (kg CO2e per USD spent)
# These are simplified, approximate figures intended for demo use only.
# Real life emissions depend on product, supply chain, manufacturing, usage and end-of-life.
# If you want, I can link real LCA sources and make these dynamic.
EMISSION_FACTORS = {
    # Electronics manufacturing and supply chain are carbon intensive per dollar.
    "Electronics (phone, laptop)": 0.30,
    # Clothing: fast fashion vs sustainable varies a lot; fast fashion higher per $.
    "Clothing (fast fashion)": 0.18,
    "Clothing (sustainable)": 0.10,
    # Food varies by type; using an average per $ for groceries (includes meat/veg mix).
    "Groceries / Food (average)": 0.22,
    "Groceries / Plant-based": 0.15,
    "Groceries / Animal-based": 0.35,
    # Air travel tickets tend to have a high CO2 per $ because of energy intensity.
    "Flight / Travel booking (ticket)": 0.55,
    # Furnishings (heavy manufacturing and transport)
    "Furniture / Home goods": 0.28,
    # Personal care and cosmetics moderate
    "Cosmetics / Personal care": 0.12,
    "Packaged goods": 0.14,
    "Books / Media": 0.09,
    "Sporting goods / Outdoor": 0.20,
    # Services and misc
    "Services / Subscriptions": 0.04,
    "Misc / Other": 0.16,
}

# Shipping distance multipliers (approximate supply chain impact)
DISTANCE_MULTIPLIERS = {
    "Local (same city)": 1.00,
    "National (within country)": 1.10,
    "International (overseas)": 1.40,
}

# Constants for conversions
KG_TO_TONNES = 1/1000
CAR_KG_PER_KM = 0.192  # average car ~192 g CO2 per km -> 0.192 kg/km
TREE_ABSORPTION_KG_PER_YEAR = 21.77  # approx. one mature tree absorbs ~21.77 kg CO2/year
PHONE_CHARGE_KG = 0.000015  # very rough: kg CO2 equivalent per phone charge

# --------------------------
# Expanded message templates and context-aware tips
FEEDBACK_TEMPLATES = [
    "Oh look — you bought {item}. The planet is so thrilled.",
    "Congrats on acquiring {item}! Earth will remember... briefly.",
    "Nice choice: {item}. Your carbon footprint applauds you silently.",
    "You ordered {item}. If guilt were measurable, it'd be in tonnes.",
    "One small purchase for you, one medium sigh from the atmosphere.",
    "You just added {item} to cart. The clouds sent a thank-you card (unsigned).",
]

# Templated tips with conditions and placeholders for context
TIPS_TEMPLATES = [
    # Generic circular-economy tips
    ({'categories': None}, "Try second-hand or refurbished for {category}. Vintage has personality and smaller emissions."),
    ({'categories': None}, "Repair before replace — local repair cafes do miracles for {category}.") ,
    ({'categories': ['Flight / Travel booking (ticket)']}, "If it's a flight: consider trains, or bundle trips and fly less often to cut emissions." ) ,
    ({'categories': ['Electronics (phone, laptop)']}, "For electronics: keep it 3–5 years longer, and recycle responsibly when done."),
    ({'categories': ['Clothing (fast fashion)','Clothing (sustainable)']}, "Choose natural fibers or properly certified sustainable brands for long-term wear.") ,
    ({'categories': ['Groceries / Animal-based']}, "Swap one animal-based meal a week for plant-based — small change, real impact."),
    ({'categories': ['Furniture / Home goods']}, "For furniture, buy solid and locally-made — heavy items travel the world already."),
    ({'categories': ['Packaged goods']}, "Avoid single-use packaging: bring your own container or buy in bulk."),
    ({'categories': None}, "Turn off fast shipping — slower delivery reduces freight emissions."),
    ({'categories': None}, "If you're feeling guilty, opt for high-quality and fewer items; it outlives the trend cycles."),
    ({'categories': None}, "Check the brand's transparency reports — transparency often means better practices."),
]

# Punchlines and short add-ons for variety
PUNCHLINES = [
    "(Future you owes present you an explanation.)",
    "(Your carbon spreadsheet has been updated.)",
    "(Mood: fashionable, atmosphere: not so much.)",
    "(This tip brought to you with minimal irony.)",
    "(Do one small thing — then another tomorrow.)",
]

SARCASTIC_SUFFIXES = [
    "(Your carbon ledger has been updated.)",
    "(No refunds accepted from atmosphere.)",
    "(Sustainability: now available as an optional extra.)",
    "(Ask again in 5–10 business years.)",
    "(This message brought to you by fossil fuels.)",
]

# --------------------------
# Utility functions

def deterministic_seed(*parts):
    base = "|".join(map(str, parts))
    h = hashlib.sha256()
    minute = datetime.utcnow().strftime("%Y%m%d%H%M")
    h.update((base + minute).encode("utf-8"))
    return int(h.hexdigest(), 16) % (2**32)


def format_kg(kg):
    if kg < 1:
        return f"{kg*1000:.0f} g CO2e"
    return f"{kg:.2f} kg CO2e"


def format_tonnes(kg):
    t = kg * KG_TO_TONNES
    return f"{t:.3f} t CO2e"

# --------------------------
# Core calculation

def estimate_emission(category: str, price_usd: float, quantity: int, distance_level: str, weight_kg: float | None, shipping_speed: str):
    """Estimate CO2e (kg) for the purchase.

    Strategy (improved):
     - Base emission = price * category_factor * quantity
     - Multiply by distance multiplier
     - Add a shipping-speed penalty (express shipping has higher emissions per order)
     - If weight provided, add a weight-based transport term
    """
    factor = EMISSION_FACTORS.get(category, EMISSION_FACTORS['Misc / Other'])
    base = price_usd * factor * quantity
    multiplier = DISTANCE_MULTIPLIERS.get(distance_level, 1.0)
    result = base * multiplier

    # shipping speed penalty
    if shipping_speed == 'Express / Overnight':
        result *= 1.15
    elif shipping_speed == 'Two-day':
        result *= 1.07

    # weight influence (mild but sensible)
    if weight_kg and weight_kg > 0:
        result += math.sqrt(weight_kg) * 1.5  # sqrt avoids runaway for heavy goods

    return max(result, 0.0)

# --------------------------
# Message generation

def choose_feedback(item_name, category, kg_co2, seed_val):
    r = random.Random(seed_val)
    tmpl = r.choice(FEEDBACK_TEMPLATES)
    suffix = r.choice(SARCASTIC_SUFFIXES)

    # intensity
    if kg_co2 < 0.5:
        intensity = 'mild'
    elif kg_co2 < 5:
        intensity = 'noticeable'
    elif kg_co2 < 50:
        intensity = 'strong'
    else:
        intensity = 'epic'

    intensity_map = {
        'mild': ["Barely a ripple.", "You could buy this daily and still be forgettable."],
        'noticeable': ["A proper puff of CO2.", "You just made a small but measurable dent."],
        'strong': ["That's the kind of purchase museums will catalog.", "Atmosphere: concerned."],
        'epic': ["Monumental. The clouds sent flowers.", "You unlocked a carbon achievement: 'The Tower'."],
    }

    line = r.choice(intensity_map[intensity])
    return f"{tmpl.format(item=item_name)} {line} {suffix}"


def choose_tip(category, distance, weight_kg, shipping_speed, seed_val):
    r = random.Random(seed_val + 7)
    # Find relevant templates
    candidates = []
    for cond, text in TIPS_TEMPLATES:
        cats = cond.get('categories')
        if cats is None or category in cats:
            candidates.append(text)

    if not candidates:
        candidates = [t for _, t in TIPS_TEMPLATES]

    tip = r.choice(candidates)

    # Fill placeholder
    tip = tip.replace('{category}', category)

    # Add conditional suggestions
    extras = []
    if shipping_speed == 'Express / Overnight':
        extras.append("Skip express shipping next time — it's pricey for the planet.")
    if weight_kg and weight_kg > 10:
        extras.append("For heavy items, prefer consolidated shipping or local pickup.")
    if distance == 'International (overseas)':
        extras.append("Check if a local equivalent exists to avoid long-haul transport.")

    # Add a punchline to keep it fun
    punch = r.choice(PUNCHLINES)
    if extras:
        tip = tip + ' ' + ' '.join(extras[:2])

    return f"{tip} {punch}"

# --------------------------
# Streamlit UI

st.set_page_config(page_title="Satirical CO2 Purchase Calculator", layout="centered")
st.title("Satirical CO2 Emissions Calculator 🛍️🌍")
st.caption("Enter a purchase and we will judge it — politely, sarcastically, and with math.")

with st.form(key='purchase_form'):
    col1, col2 = st.columns([2, 1])
    with col1:
        item_name = st.text_input("Item name (e.g. 'AirPods Pro', 'Red T-shirt'):")
    with col2:
        category = st.selectbox("Category", list(EMISSION_FACTORS.keys()))

    price = st.number_input("Price (USD)", min_value=0.0, value=49.99, step=1.0, format='%.2f')
    quantity = st.number_input("Quantity", min_value=1, value=1, step=1)
    weight = st.number_input("Approx weight (kg, optional, 0 if unknown)", min_value=0.0, value=0.0, step=0.1)

    distance = st.selectbox("Shipping distance/scale", list(DISTANCE_MULTIPLIERS.keys()))
    shipping_speed = st.selectbox("Shipping speed", ['Standard (5–8 days)', 'Two-day', 'Express / Overnight'])
    donate_offset = st.checkbox("Donate to offsets (I know it's a compromise)")

    submitted = st.form_submit_button("Calculate my guilt")

if submitted:
    seed_val = deterministic_seed(item_name, category, price, quantity, weight, distance, shipping_speed)

    kg = estimate_emission(category, price, int(quantity), distance, weight if weight > 0 else None, shipping_speed)

    # pretend donation reduces 10% (still satire)
    if donate_offset:
        kg_after = kg * 0.90
    else:
        kg_after = kg

    st.header("Your Purchase Emissions")
    st.markdown(f"**Item:** {item_name or '— unnamed purchase —'}  ")
    st.markdown(f"**Category:** {category}  ")
    st.markdown(f"**Estimated emissions:** **{format_kg(kg_after)}** ({format_tonnes(kg_after)})")

    car_km = kg_after / CAR_KG_PER_KM if CAR_KG_PER_KM > 0 else 0
    tree_years = kg_after / TREE_ABSORPTION_KG_PER_YEAR
    phone_charges = kg_after / PHONE_CHARGE_KG

    st.write(f"Equivalent to driving ~{car_km:,.0f} km by car.")
    st.write(f"Equivalent to the CO2 absorbed by ~{tree_years:.1f} tree-years.")
    st.write(f"Equivalent to ~{phone_charges:,.0f} phone charges (because why not?).")

    feedback = choose_feedback(item_name or category, category, kg_after, seed_val)
    tip = choose_tip(category, distance, weight, shipping_speed, seed_val)

    st.subheader("Sarcastic feedback")
    st.info(feedback)

    st.subheader("Sustainability tip (context-aware and varied)")
    st.success(tip)

    if 'history' not in st.session_state:
        st.session_state.history = []
    st.session_state.history.insert(0, {
        'time': datetime.utcnow().isoformat() + 'Z',
        'item': item_name,
        'category': category,
        'price': price,
        'quantity': quantity,
        'kg_co2': round(kg_after, 3),
    })

    st.write('---')
    st.subheader('Recent calculations (this session)')
    for h in st.session_state.history[:7]:
        st.write(f"• {h['time']}: {h['item'] or h['category']} — {h['kg_co2']} kg CO2e (${h['price']})")

    # Fixed unterminated string issue: use a properly closed string here
    st.write("---")
    st.caption("Disclaimer: This calculator is satirical and uses simplified estimations. For robust carbon accounting consult detailed LCA databases and experts.")

else:
    st.write("Fill the form above and click 'Calculate my guilt' to get your sarcastic sustainability report.")

# End of file
