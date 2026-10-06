"""Presentation-only checks; detector values and functional tests stay unchanged."""
import json
from copy import deepcopy
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from bank_app.services.filter_adapter import FilterAnalysis
from bank_app.state.bank_state import BankState


def detector_view():
    import streamlit as st
    from bank_app.components.manual_transaction import render_detector_information
    render_detector_information(st.session_state['analysis'], st.session_state['raw'])


@pytest.mark.parametrize('recurring,kind,level,confidence,expected', [
    (True, 'SUBSCRIPTION', 'MERCHANT_MODEL+TYPE_ENGINE', .985467,
     ('Sí', 'Suscripción', 'Modelo histórico + análisis de tipo', '98.55%')),
    (False, 'NON_RECURRING', 'INSUFFICIENT_EVIDENCE', .30000000000000004,
     ('No', 'No recurrente', 'Evidencia insuficiente', '30.00%')),
    (True, 'RECURRING_BILL', 'NETWORK_EXPLICIT', .99,
     ('Sí', 'Cobro recurrente', 'Señal explícita de la red', '99.00%')),
    (True, 'FUTURE_TYPE', 'FUTURE_LEVEL', .8,
     ('Sí', 'FUTURE_TYPE', 'FUTURE_LEVEL', '80.00%')),
])
def test_friendly_detector_view_preserves_technical_data(recurring, kind, level, confidence, expected):
    reasons = [
        'E-commerce transaction', 'Stored credential', 'Card-not-present transaction',
        'Merchant historical model: 98.55%', 'Merchant customers observed: 289',
        'Repeat customer rate: 95.85%', 'Recurring interval regularity: 100.00%',
        'Amount similarity: 100.00%', 'MCC 4899 is subscription/membership-oriented',
        'Future evidence: retain original text',
    ]
    analysis = FilterAnalysis(recurring, kind, confidence, .85, level, False, None, reasons)
    original = deepcopy(analysis)
    raw = {'customer_id': 'MANUAL_CUSTOMER', 'merchant_id': 'SPOTIFY001'}
    app = AppTest.from_function(detector_view)
    app.session_state['analysis'] = analysis
    app.session_state['raw'] = raw
    app.run()
    assert not app.exception
    outer = app.expander[0]
    technical = next(e for e in outer.expander if e.label == 'Ver datos técnicos')
    assert not technical.proto.expanded
    friendly = '\n'.join(m.value for m in outer.markdown)
    for label, value in zip(
        ['¿Es un cobro recurrente?', 'Tipo detectado', 'Nivel de detección', 'Confianza de recurrencia'],
        expected,
    ):
        assert f'**{label}:** {value}' in friendly
    assert '**Confianza del tipo:** 85.00%' in friendly
    for reason in [
        'Transacción de comercio electrónico', 'Tarjeta guardada en el comercio',
        'Transacción sin presencia del titular', 'Modelo histórico del comercio: 98.55%',
        'Clientes observados: 289', 'Tasa de clientes recurrentes: 95.85%',
        'Regularidad de los intervalos: 100.00%', 'Similitud del monto: 100.00%',
        'MCC 4899 asociado a suscripciones o membresías', reasons[-1],
    ]:
        assert f'• {reason}' in friendly
    assert '0.30000000000000004' not in friendly
    assert 'customer_id' not in friendly and 'merchant_id' not in friendly
    assert json.loads(technical.json[0].value) == {
        name: getattr(original, name) for name in (
            'is_recurring', 'recurring_type', 'recurrence_confidence',
            'type_confidence', 'detection_level', 'reasons',
        )
    }
    assert json.loads(technical.json[1].value) == raw
    assert analysis == original
    assert len(outer.json) == len(technical.json) == 2
    assert list(outer.children.values())[-1].label == 'Ver datos técnicos'


def test_manual_none_message_describes_insufficient_evidence():
    app_path = Path(__file__).resolve().parents[1] / 'bank_app' / 'app.py'
    app = AppTest.from_file(str(app_path), default_timeout=15)
    app.session_state['bank_state'] = BankState()
    app.session_state['selected_page'] = 'Simulador'
    app.run()
    app.segmented_control(key='first-charge-scenario').set_value('Crear cobro manual').run()
    app.text_input(key='manual-merchant').set_value('GIMNASIO PRUEBA')
    app.text_input(key='manual-mcc').set_value('7997')
    app.button(key='process-manual-charge').click().run()
    assert not app.exception
    messages = [s.value for s in app.success]
    assert 'El filtro no encontró evidencia suficiente para clasificar este cobro como recurrente.' in messages
    assert 'Transacción procesada como compra normal.' not in messages
