import streamlit as st

from bank_app.data.demo_data import seed_demo_data
from bank_app.state.bank_state import BankState


BANK_STATE_KEY = "bank_state"


def initialize_bank_state() -> BankState:
    """
    Crea el estado inicial del gemelo digital.
    """

    if BANK_STATE_KEY not in st.session_state:

        bank = BankState()

        seed_demo_data(bank)

        st.session_state[BANK_STATE_KEY] = bank

    return st.session_state[BANK_STATE_KEY]


def get_bank_state() -> BankState:
    """
    Devuelve el estado actual del banco.
    """

    return initialize_bank_state()


def reset_bank_state() -> BankState:
    """
    Restaura completamente el escenario inicial
    del gemelo digital.
    """

    bank = BankState()

    seed_demo_data(bank)

    st.session_state[BANK_STATE_KEY] = bank

    return bank