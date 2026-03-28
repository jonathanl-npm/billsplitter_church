import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from streamlit_autorefresh import st_autorefresh

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="KLGCC Outing 🎳",
    page_icon="🎳",
    layout="centered"
)

st_autorefresh(interval=5000, key="sync_refresh")

RESET_PASSWORD = "admin123"  # Change this to your preferred password

# ── Mobile-friendly CSS ───────────────────────────────────────────────────────
st.markdown("""
    <style>
        /* Larger base font */
        html, body, [class*="css"] {
            font-size: 16px !important;
        }

        /* Bigger checkbox tap targets */
        input[type="checkbox"] {
            width: 22px !important;
            height: 22px !important;
            cursor: pointer;
        }

        /* Item text easier to read */
        .item-label {
            font-size: 15px;
            line-height: 1.5;
            padding: 4px 0;
        }

        /* Make buttons bigger on mobile */
        .stButton > button {
            height: 52px !important;
            font-size: 16px !important;
            border-radius: 10px !important;
        }

        /* Tighten up columns on small screens */
        [data-testid="column"] {
            padding: 2px !important;
        }

        /* Input field larger */
        .stTextInput input {
            font-size: 16px !important;
            height: 48px !important;
        }
    </style>
""", unsafe_allow_html=True)

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
        "total": round(3.24 + 2 * 11.57, 2)
    }
    for i in range(1, 12)
]
BOWLING_TOTAL = round(11 * 26.38, 2)

ALL_ITEMS = BIG_LEAF + ABADI + KLGCC_BOWLING

# ── Google Sheets ─────────────────────────────────────────────────────────────

@st.cache_resource
def get_sheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
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
    claimed_count = sum(1 for i in items if i["id"] in claimed)
    all_done = claimed_count == len(items)
    status = "✅ All claimed" if all_done else f"{claimed_count}/{len(items)} claimed"

    with st.expander(f"{title} — RM {grand_total:.2f}  |  {status}", expanded=True):
        running = 0.0
        for item in items:
            iid = item["id"]
            claimer = claimed.get(iid)

            if claimer:
                col1, col2 = st.columns([0.08, 0.92])
                with col1:
                    st.checkbox("", value=True, disabled=True, key=f"chk_{iid}")
                with col2:
                    st.markdown(
                        f"<div class='item-label' style='color:gray;'>"
                        f"<s>{item['item']}</s> &nbsp;·&nbsp; "
                        f"<em>{claimer}</em> &nbsp;·&nbsp; RM {item['total']:.2f}"
                        f"</div>",
                        unsafe_allow_html=True
                    )
            else:
                checked = iid in st.session_state.pending
                col1, col2 = st.columns([0.08, 0.92])
                with col1:
                    ticked = st.checkbox("", value=checked, key=f"chk_{iid}")
                with col2:
                    st.markdown(
                        f"<div class='item-label'>"
                        f"{item['item']} &nbsp;·&nbsp; RM {item['total']:.2f}"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                if ticked:
                    st.session_state.pending.add(iid)
                    running += item["total"]
                else:
                    st.session_state.pending.discard(iid)

        return running

# ── Main UI ───────────────────────────────────────────────────────────────────

st.title("🎳 KLGCC Outing")
st.caption("Tap your items, enter your name, then hit Submit. · 💳 Pay via TNG or DuitNow to 0125118233")

name = st.text_input("Your name", placeholder="e.g. Ali")

claimed = load_claimed()

total  = render_receipt("🍽️ Big Leaf", BIG_LEAF, 250.20, claimed)
total += render_receipt("☕ Abadi Cafeteria", ABADI, 34.10, claimed)
total += render_receipt("🎳 Bowling — KLGCC", KLGCC_BOWLING, BOWLING_TOTAL, claimed)

if total > 0:
    st.success(f"**Your selection: RM {total:.2f}**")

# ── Submit & Reset ────────────────────────────────────────────────────────────

col_submit, col_reset = st.columns(2)

with col_submit:
    if st.button("✅ Submit", use_container_width=True, type="primary"):
        if not name.strip():
            st.error("Please enter your name.")
        elif not st.session_state.pending:
            st.error("Please select at least one item.")
        else:
            save_claimed(st.session_state.pending, name.strip())
            st.session_state.pending.clear()
            st.success(f"✅ Done, **{name.strip()}**! Pay RM {total:.2f} via TNG/DuitNow to 0125118233")
            st.rerun()

with col_reset:
    if st.button("🔄 Reset (Admin)", use_container_width=True):
        st.session_state.show_reset_prompt = True

if st.session_state.show_reset_prompt:
    pwd = st.text_input("Admin password:", type="password", key="reset_pwd")
    if st.button("Confirm Reset"):
        if pwd == RESET_PASSWORD:
            reset_all()
            st.session_state.pending.clear()
            st.session_state.show_reset_prompt = False
            st.success("All claims reset.")
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

    st.markdown(f"**Total Claimed: RM {sum(summary.values()):.2f}**")
