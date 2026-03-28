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
        sheet.append_row([iid,
