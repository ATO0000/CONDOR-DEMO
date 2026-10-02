import streamlit as st


def inject_global_styles() -> None:
    st.markdown(
        """
        <style>

        /* ====================================================
           BASE
        ==================================================== */

        .stApp {
            background: #f6f7f9;
        }

        .block-container {
            max-width: 1120px;
            padding-top: 2.2rem;
            padding-bottom: 4rem;
        }

        [data-testid="stMain"] {
            color: #1b2430;
        }

        [data-testid="stMain"] h1 {
            color: #182230;
            font-size: 2rem;
            font-weight: 650;
            letter-spacing: -0.035em;
        }

        [data-testid="stMain"] h2 {
            color: #182230;
            font-size: 1.25rem;
            font-weight: 650;
            letter-spacing: -0.02em;
        }

        [data-testid="stMain"] h3 {
            color: #182230;
            font-size: 1rem;
            font-weight: 650;
        }

        [data-testid="stCaptionContainer"] {
            color: #747d8a;
        }


        /* ====================================================
        SIDEBAR
        ==================================================== */

        section[data-testid="stSidebar"],
        section[data-testid="stSidebar"] > div,
        [data-testid="stSidebarContent"] {
            background-color: #102a43 !important;
        }

        /* Texto general */

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label {
            color: #f5f7fa !important;
        }

        section[data-testid="stSidebar"] hr {
            border-color: rgba(255,255,255,0.12) !important;
        }


        /* ====================================================
        SIDEBAR NAVIGATION BUTTONS
        ==================================================== */

        section[data-testid="stSidebar"] .stButton {
            margin-bottom: 0.15rem;
        }

        section[data-testid="stSidebar"] .stButton > button {
            width: 100%;
            justify-content: flex-start !important;
            text-align: left !important;
            padding-left: 0.85rem !important;
            min-height: 2.7rem;
            border-radius: 7px !important;
            box-shadow: none !important;
            color: #f5f7fa !important;
        }

        /* Inactivos */

        section[data-testid="stSidebar"]
        .stButton > button[kind="tertiary"] {
            background: transparent !important;
            border: none !important;
            color: #f5f7fa !important;
        }

        section[data-testid="stSidebar"]
        .stButton > button[kind="tertiary"]:hover {
            background: rgba(255,255,255,0.07) !important;
            color: #ffffff !important;
        }

        /* Activo */

        section[data-testid="stSidebar"]
        .stButton > button[kind="primary"] {
            background: rgba(255,255,255,0.13) !important;
            border: none !important;
            color: #ffffff !important;
        }

        section[data-testid="stSidebar"]
        .stButton > button[kind="primary"]:hover {
            background: rgba(255,255,255,0.16) !important;
        }


        /* ====================================================
        RESET DEMO
        ==================================================== */

        section[data-testid="stSidebar"] .st-key-reset-demo button {
            justify-content: center !important;
            text-align: center !important;
            background: transparent !important;
            border: 1px solid rgba(255,255,255,0.25) !important;
            color: #ffffff !important;
        }

        section[data-testid="stSidebar"] .st-key-reset-demo button:hover {
            background: rgba(255,255,255,0.07) !important;
            border-color: rgba(255,255,255,0.40) !important;
        }



        /* ====================================================
           STREAMLIT CONTROLS
        ==================================================== */

        .stButton > button {
            border-radius: 7px;
            min-height: 2.65rem;
            font-weight: 600;
            box-shadow: none;
        }

        .stButton > button[kind="primary"] {
            background: #1261a6;
            border-color: #1261a6;
        }

        [data-testid="stVerticalBlockBorderWrapper"] {
            background: #ffffff;
            border: 1px solid #e3e7ec;
            border-radius: 9px;
        }

        [data-testid="stExpander"] {
            background: #ffffff;
            border: 1px solid #e3e7ec;
            border-radius: 8px;
        }

        button[data-baseweb="tab"] {
            font-weight: 600;
        }

        


        /* ====================================================
           PAGE HEADER
        ==================================================== */

        .page-heading {
            margin-bottom: 1.6rem;
        }

        .page-heading .subtitle {
            color: #6c7683;
            font-size: 0.95rem;
            margin-top: -0.35rem;
        }


        /* ====================================================
           ACCOUNT
        ==================================================== */

        .account-card {
            background: #ffffff;
            border: 1px solid #dfe4ea;
            border-radius: 10px;
            padding: 1.45rem 1.55rem;
            margin-bottom: 1rem;
        }

        .account-top {
            display: flex;
            justify-content: space-between;
            align-items: start;
            gap: 1rem;
        }

        .account-label {
            color: #707986;
            font-size: 0.82rem;
            font-weight: 600;
        }

        .account-balance {
            color: #172230;
            font-size: 2rem;
            font-weight: 650;
            letter-spacing: -0.035em;
            margin-top: 0.25rem;
        }

        .account-number {
            color: #7b8490;
            font-size: 0.82rem;
            margin-top: 0.35rem;
        }

        .account-type {
            color: #334155;
            font-size: 0.85rem;
            font-weight: 600;
        }


        /* ====================================================
           SUMMARY
        ==================================================== */

        .summary-strip {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            background: #ffffff;
            border: 1px solid #e2e6eb;
            border-radius: 9px;
            margin-bottom: 1.15rem;
        }

        .summary-item {
            padding: 1rem 1.15rem;
            border-right: 1px solid #e8ebef;
        }

        .summary-item:last-child {
            border-right: 0;
        }

        .summary-label {
            color: #77808c;
            font-size: 0.77rem;
            margin-bottom: 0.25rem;
        }

        .summary-value {
            color: #1c2733;
            font-size: 1.2rem;
            font-weight: 650;
        }


        /* ====================================================
           PROTECTION STATUS
        ==================================================== */

        .protection-card {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            background: #ffffff;
            border: 1px solid #e2e6eb;
            border-radius: 9px;
            padding: 1rem 1.15rem;
            margin-bottom: 1.8rem;
        }

        .protection-title {
            color: #283442;
            font-size: 0.9rem;
            font-weight: 650;
        }

        .protection-copy {
            color: #77808c;
            font-size: 0.8rem;
            margin-top: 0.15rem;
        }


        /* ====================================================
           PILLS
        ==================================================== */

        .pill {
            display: inline-block;
            padding: 0.27rem 0.55rem;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 650;
            white-space: nowrap;
        }

        .pill-ok {
            color: #17603a;
            background: #eaf5ee;
        }

        .pill-watch {
            color: #795600;
            background: #fff5d6;
        }

        .pill-alert {
            color: #9a2c2c;
            background: #fdecec;
        }

        .pill-neutral {
            color: #53606d;
            background: #eef1f4;
        }


        /* ====================================================
           LISTS
        ==================================================== */

        .bank-list {
            background: #ffffff;
            border: 1px solid #e2e6eb;
            border-radius: 9px;
            overflow: hidden;
        }

        .bank-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            padding: 0.9rem 1rem;
            border-bottom: 1px solid #edf0f3;
        }

        .bank-row:last-child {
            border-bottom: 0;
        }

        .row-main {
            min-width: 0;
        }

        .row-title {
            color: #26323f;
            font-size: 0.9rem;
            font-weight: 600;
        }

        .row-subtitle {
            color: #848c96;
            font-size: 0.76rem;
            margin-top: 0.13rem;
        }

        .row-amount {
            color: #26323f;
            font-size: 0.9rem;
            font-weight: 650;
            white-space: nowrap;
        }

        .section-title {
            color: #25313d;
            font-size: 1rem;
            font-weight: 650;
            margin-bottom: 0.65rem;
        }

        /* ====================================================
        DEMO / SIMULATOR
        ==================================================== */

        .demo-banner {
            display: flex;
            align-items: flex-start;
            gap: 0.9rem;
            background: #eef4fa;
            border: 1px solid #d5e2ef;
            border-radius: 8px;
            padding: 1rem 1.1rem;
            margin-bottom: 1.5rem;
        }

        .demo-badge {
            display: inline-block;
            color: #174d7c;
            background: #dceaf7;
            border-radius: 999px;
            padding: 0.25rem 0.55rem;
            font-size: 0.7rem;
            font-weight: 700;
            white-space: nowrap;
        }

        .demo-title {
            color: #253747;
            font-size: 0.9rem;
            font-weight: 650;
        }

        .demo-copy {
            color: #667685;
            font-size: 0.8rem;
            line-height: 1.45;
            margin-top: 0.18rem;
        }

        .scenario-box {
            background: #ffffff;
            border-left: 3px solid #1261a6;
            padding: 0.75rem 0.95rem;
            margin-bottom: 1.2rem;
        }

        .scenario-title {
            color: #263746;
            font-size: 0.86rem;
            font-weight: 650;
        }

        .scenario-copy {
            color: #74808c;
            font-size: 0.78rem;
            margin-top: 0.15rem;
        }
        /* ====================================================
           RESPONSIVE
        ==================================================== */

        @media (max-width: 800px) {

            .summary-strip {
                grid-template-columns: repeat(2, 1fr);
            }

            .summary-item:nth-child(2) {
                border-right: 0;
            }

            .summary-item:nth-child(-n+2) {
                border-bottom: 1px solid #e8ebef;
            }

            .protection-card,
            .account-top {
                flex-direction: column;
            }
        }

        </style>
        """,
        unsafe_allow_html=True,
    )