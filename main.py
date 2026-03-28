import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from streamlit_autorefresh import st_autorefresh

st_autorefresh(interval=5000, key="sync_refresh")

RESET_PASSWORD = "admin123"  # Change this to your preferred password

# ── Data ──────────────────────────────────────────────────────────────────────

BIG_LEAF = [
    {"id": "bl_01", "item": "Teh Tarik (1)",                               "total": 4.06},
    {"id": "bl_02", "item": "Warm Water",                                   "total": 0.58},
    {"id": "bl_03", "item": "Fried Chicken - Breast",                       "total": 9.16},
    {"id": "bl_04", "item": "Banana Leaf Rice Meal (1)",                    "total": 14.50},
    {"id": "bl_05", "item": "Banana Leaf Rice Meal (2)",                    "total": 14.50},
    {"id": "bl_06", "item": "Banana Leaf Rice Meal (3)",                    "total": 14.50},
    {"id": "bl_07", "item": "Banana Leaf Rice Meal (4)",                    "total": 14.50},
    {"id": "bl_08", "item": "Banana Leaf Rice Meal (5)",                    "total": 14.50},
    {"id": "bl_09", "item": "Banana Leaf Rice Meal (6)",                    "total": 14.50},
    {"id": "bl_10", "item": "Ice Water",                                    "total": 0.58},
    {"id": "bl_11", "item": "Chicken 65",                                   "total": 13.34},
    {"id": "bl_12", "item": "Fried Tenggiri (1)",                           "total": 15.08},
    {"id": "bl_13", "item": "Fried Tenggiri (2)",                           "total": 15.08},
    {"id": "bl_14", "item": "Mutton Masala",                                "total": 18.56},
    {"id": "bl_15", "item": "Chicken Varuval (1)",                          "total": 12.64},
    {"id": "bl_16", "item": "Chicken Varuval (2)",                          "total": 12.64},
    {"id": "bl_17", "item": "Teh Tarik (2)",                                "total": 4.06},
    {"id": "bl_18", "item": "Tandoori Chicken Combo - Garlic Butter Naan",  "total": 25.40},
    {"id": "bl_19", "item": "Coke Zero",                                    "total": 4.52},
    {"id": "bl_20", "item": "Biryani Rice - Chicken Curry (1)",             "total": 9.16},
    {"id": "bl_21", "item": "Biryani Rice - Chicken Curry (2)",             "total": 9.16},
    {"id": "bl_22", "item": "Fried Chicken - Drumstick",                    "total": 9.16},
]

ABADI = [
    {"id": "ab_01", "item": "Air Suam (1)",         "total": 0.40},
    {"id": "ab_02", "item": "Air Suam (2)",         "total": 0.40},
    {"id": "ab_03", "item": "Limau Ais (1)",        "total": 3.10},
    {"id": "ab_04", "item": "Teh O Limau Ais (1)",  "total": 3.40},
    {"id": "ab_05", "item": "Teh O Limau Ais (2)",  "total": 3.40},
    {"id": "ab_06", "item": "Milo Ais",             "total": 4.70},
    {"id": "ab_07", "item": "Limau Panas (1)",      "total": 2.00},
    {"id": "ab_08", "item": "Sirap Bandung Ais",    "total": 3.70},
    {"id": "ab_09", "item": "Limau Ais (2)",        "total": 3.10},
    {"id": "ab_10", "item": "Teh Tarik",            "total": 2.50},
    {"id": "ab_11", "item": "Limau Ais (3)",        "total": 2.70},
    {"id": "ab_12", "item": "Limau Panas (2)",      "total": 2.00},
    {"id": "ab_13", "item": "Limau Ais (4)",        "total": 2.70},
]

KLGCC_BOWLING = [
    {
        "id": f"bw_{i:02d}",
        "item": f"Bowling Package ({i}) — Shoe Rental + 2 Games",
        "total": round(3.24 + 2 * 11.57, 2)  # RM 26.38 per person
    }
    for i in range(1, 12)
]
BOWLING_TOTAL = round(11 * 26.38, 2)  # RM 290.18

ALL_ITEMS = BIG_LEAF + ABADI + KLGCC_BOWLING

# ── Google Sheets ─────────────────────────────────────────────────────────────

@st.cache_resource
def get_sheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"  # required by gspread
        ]
    )
    client = gspread.authorize(creds)
    return client.open("BillSplitter").sheet1

def load_claimed():
    try:
        records = get_sheet().get_all_records()
        return {r["item_id"]: r["claimer"] for r in records}
    except Exception:
        return {}

def save_claimed(item_ids, name):
    sheet = get_sheet()
    for iid in item_ids:
        sheet.append_row([iid, name])

def reset_all():
    sheet = get_sheet()
    sheet.clear()
    sheet.append_row(["item_id", "claimer"])

# ── Session State ─────────────────────────────────────────────────────────────

if "pending" not in st.session_state:
    st.session_state.pending = set()
if "show_reset_prompt" not in st.session_state:
    st.session_state.show_reset_prompt = False

# ── Renderer ──────────────────────────────────────────────────────────────────

def render_receipt(title, items, grand_total, claimed):
    st.subheader(title)
    st.caption(f"Grand Total: RM {grand_total:.2f}")

    running = 0.0
    for item in items:
        iid = item["id"]
        claimer = claimed.get(iid)
        col1, col2, col3 = st.columns([0.08, 0.62, 0.30])

        if claimer:
            with col1:
                st.checkbox("", value=True, disabled=True, key=f"chk_{iid}")
            with col2:
                st.markdown(f"~~{item['item']}~~ — *{claimer}*")
            with col3:
                st.markdown(f"RM {item['total']:.2f}")
        else:
            checked = iid in st.session_state.pending
            with col1:
                ticked = st.checkbox("", value=checked, key=f"chk_{iid}")
            with col2:
                st.markdown(item["item"])
            with col3:
                st.markdown(f"RM {item['total']:.2f}")
            if ticked:
                st.session_state.pending.add(iid)
                running += item["total"]
            else:
                st.session_state.pending.discard(iid)

    return running

# ── Main UI ───────────────────────────────────────────────────────────────────

st.title("🎳 Bill Splitter — KLGCC Outing")
st.markdown("Select your items across all receipts, enter your name, then tap **Submit**.")
st.info("💳 Please pay via **TNG or DuitNow** to **0125118233**")

name = st.text_input("Your name", placeholder="e.g. Ali")

claimed = load_claimed()

st.divider()
total  = render_receipt("🍽️ Big Leaf", BIG_LEAF, 250.20, claimed)
st.divider()
total += render_receipt("☕ Abadi Cafeteria", ABADI, 34.10, claimed)
st.divider()
total += render_receipt("🎳 Bowling — KLGCC", KLGCC_BOWLING, BOWLING_TOTAL, claimed)
st.divider()

if total > 0:
    st.success(f"**Your current selection: RM {total:.2f}**")

# ── Submit & Reset ────────────────────────────────────────────────────────────

col_submit, col_reset = st.columns(2)

with col_submit:
    if st.button("✅ Submit", use_container_width=True, type="primary"):
        if not name.strip():
            st.error("Please enter your name before submitting.")
        elif not st.session_state.pending:
            st.error("Please select at least one item.")
        else:
            save_claimed(st.session_state.pending, name.strip())
            st.session_state.pending.clear()
            st.success(f"Claimed by **{name.strip()}**! Total: RM {total:.2f} — please pay via TNG or DuitNow to 0125118233")
            st.rerun()

with col_reset:
    if st.button("🔄 Reset All (Admin)", use_container_width=True):
        st.session_state.show_reset_prompt = True

if st.session_state.show_reset_prompt:
    pwd = st.text_input("Enter admin password:", type="password", key="reset_pwd")
    if st.button("Confirm Reset"):
        if pwd == RESET_PASSWORD:
            reset_all()
            st.session_state.pending.clear()
            st.session_state.show_reset_prompt = False
            st.success("All claims have been reset.")
            st.rerun()
        else:
            st.error("Incorrect password.")

# ── Summary ───────────────────────────────────────────────────────────────────

if claimed:
    st.divider()
    st.subheader("📊 Summary")
    summary = {}
    for item in ALL_ITEMS:
        claimer = claimed.get(item["id"])
        if claimer:
            summary[claimer] = summary.get(claimer, 0.0) + item["total"]

    for person, amt in sorted(summary.items()):
        st.markdown(f"- **{person}**: RM {amt:.2f}")

    total_claimed = sum(summary.values())

    # Only show total claimed, no unclaimed amount shown
    st.markdown(f"**Total Claimed: RM {total_claimed:.2f}**")
