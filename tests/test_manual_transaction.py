from pathlib import Path
from unittest.mock import Mock

import pytest
from streamlit.testing.v1 import AppTest

from bank_app.components.simulator import load_evaluation_transactions
from bank_app.services import filter_adapter, incoming_transaction_service as incoming
from bank_app.services.filter_adapter import FilterAnalysis
from bank_app.services.manual_transaction_service import build_manual_transaction
from bank_app.services.subscription_detection_policy import decide_subscription_action
from bank_app.state.bank_state import BankState

APP = Path(__file__).resolve().parents[1] / "bank_app" / "app.py"
LABELS = ["Sí, es una suscripción", "No estoy seguro", "No es una suscripción"]


def build(**overrides):
    values = dict(merchant=" PRUEBA ", amount=5290, mcc="4899", network="VISA",
                  ecommerce=True, stored_credential=True)
    return build_manual_transaction(**(values | overrides))


def test_valid_manual_transaction_and_unique_ids():
    first, second = build(), build()
    assert first['merchant'] == 'PRUEBA'
    assert first['amount'] == 5290
    assert first['currency'] == 'CLP'
    assert first['mcc'] == '4899'
    assert first['customer_id'] != second['customer_id']
    assert first['merchant_id'] != second['merchant_id']
    assert 'true_type' not in first
    assert 'merchant_subscription_probability' not in first
    assert first['cit_mit_indicator'] is None
    assert first['three_ds_recurring'] is None


@pytest.mark.parametrize('overrides', [
    {'merchant': ''}, {'merchant': '  '}, {'amount': 0}, {'amount': -1},
    {'amount': True}, {'amount': 1.5}, {'amount': float('inf')},
    {'mcc': ''}, {'mcc': '123'}, {'mcc': '12345'}, {'mcc': 'abcd'}, {'mcc': '１２３４'},
    {'network': 'OTHER'}, {'customer_id': 'a|b'}, {'merchant_id': 'a|b'},
    {'ecommerce': None}, {'stored_credential': 'Sí'}, {'cardholder_present': 1},
    {'cit_mit_indicator': 'MIT'}, {'pos_environment': 'OTHER'}, {'three_ds_recurring': 'true'},
])
def test_invalid_form_values(overrides):
    with pytest.raises(ValueError):
        build(**overrides)


def test_normalization_and_explicit_signals():
    raw = build(merchant_id=' SPOTIFY001 ', customer_id=' custom ', network=' mastercard ',
                mcc=' 0123 ', cit_mit_indicator='M103', pos_environment='C',
                cardholder_present=False, three_ds_recurring=True,
                ecommerce=False, stored_credential=False)
    assert raw['merchant_id'] == 'SPOTIFY001'
    assert raw['customer_id'] == 'custom'
    assert raw['network'] == 'MASTERCARD'
    assert raw['mcc'] == '0123'
    assert raw['cit_mit_indicator'] == 'M103'
    assert raw['three_ds_recurring'] is True
    assert raw['ecommerce'] is raw['stored_credential'] is False


def test_spotify_equivalent_uses_real_pipeline(monkeypatch):
    source = next(t for t in load_evaluation_transactions() if t['merchant_id'] == 'SPOTIFY001')
    source.pop('true_type')
    source.pop('currency')
    raw = build_manual_transaction(**source)
    expected = filter_adapter.analyze_bank_transaction(raw)
    pipeline = Mock(wraps=filter_adapter.analyze_transaction)
    adapter = Mock(wraps=incoming.analyze_bank_transaction)
    monkeypatch.setattr(filter_adapter, 'analyze_transaction', pipeline)
    monkeypatch.setattr(incoming, 'analyze_bank_transaction', adapter)
    bank = BankState()
    transaction, actual = incoming.process_incoming_transaction(bank, raw)
    adapter.assert_called_once_with(raw)
    pipeline.assert_called_once()
    assert actual == expected
    assert decide_subscription_action(actual).value == 'AUTO_DETECTED'
    assert bank.transactions == [transaction]
    subscription, = bank.subscriptions
    assert subscription.status.value == 'ACTIVE'
    assert subscription.trust_status.value == 'UNTRUSTED'
    assert not bank.subscription_candidates


def test_unknown_merchant_no_name_matching_and_no_double_debit():
    bank = BankState()
    raw = build(merchant='SPOTIFY', merchant_id='MANUAL_UNKNOWN_001')
    transaction, analysis = incoming.process_incoming_transaction(bank, raw)
    assert bank.transactions == [transaction]
    assert decide_subscription_action(analysis).value == 'NONE'
    assert not bank.subscriptions
    balance = bank.balance
    with pytest.raises(ValueError, match='ya fue procesada'):
        incoming.process_incoming_transaction(bank, raw)
    assert bank.balance == balance
    assert len(bank.transactions) == 1


def manual_app():
    app = AppTest.from_file(str(APP), default_timeout=15)
    app.session_state['bank_state'] = BankState()
    app.session_state['selected_page'] = 'Simulador'
    app.run()
    assert 'Crear cobro manual' in app.segmented_control(key='first-charge-scenario').options
    app.segmented_control(key='first-charge-scenario').set_value('Crear cobro manual').run()
    assert not app.exception
    assert not any('Escenario controlado' in str(getattr(e, 'value', '')) for e in app)
    return app


def fill(app, merchant='PRUEBA', merchant_id=''):
    app.text_input(key='manual-merchant').set_value(merchant)
    app.text_input(key='manual-mcc').set_value('4899')
    app.text_input(key='manual-merchant-id').set_value(merchant_id)
    return app


def submit(app):
    app.button(key='process-manual-charge').click().run()
    assert not app.exception
    return app


def test_manual_ui_real_pipeline_receipt_movements_and_reruns(monkeypatch):
    pipeline = Mock(wraps=filter_adapter.analyze_transaction)
    service = Mock(wraps=incoming.process_incoming_transaction)
    monkeypatch.setattr(filter_adapter, 'analyze_transaction', pipeline)
    monkeypatch.setattr('bank_app.components.manual_transaction.process_incoming_transaction', service)
    app = submit(fill(manual_app()))
    assert not app.error
    assert 'Analizado por el filtro real' in [s.value for s in app.success]
    assert 'Información del detector' in [e.label for e in app.expander]
    service.assert_called_once()
    pipeline.assert_called_once()
    raw = service.call_args.args[1]
    assert 'true_type' not in raw
    bank = app.session_state['bank_state']
    assert len(bank.transactions) == 1
    balance = bank.balance
    app.run()
    assert bank.balance == balance
    assert len(bank.transactions) == 1
    app.session_state['selected_page'] = 'Movimientos'
    app.run()
    assert not app.exception
    assert any('PRUEBA' in str(getattr(e, 'value', '')) for e in app)
    app.session_state['selected_page'] = 'Simulador'
    app.run()
    app.segmented_control(key='first-charge-scenario').set_value('Crear cobro manual').run()
    app.button(key='new-manual-charge').click().run()
    submit(fill(app))
    assert len(bank.transactions) == 2
    assert len(bank.processed_demo_transactions) == 2
    app.button(key='reset-demo').click().run()
    assert not app.exception
    app.segmented_control(key='first-charge-scenario').set_value('Crear cobro manual').run()
    assert 'Analizado por el filtro real' not in [s.value for s in app.success]
    assert app.button(key='process-manual-charge')


def test_manual_ui_validation_and_custom_key_duplicate():
    app = submit(manual_app())
    assert app.error
    assert not app.session_state['bank_state'].transactions
    fill(app)
    app.text_input(key='manual-customer-id').set_value('CUSTOM')
    app.text_input(key='manual-merchant-id').set_value('MANUAL_GYM_001')
    submit(app)
    bank = app.session_state['bank_state']
    balance = bank.balance
    app.button(key='new-manual-charge').click().run()
    fill(app, merchant_id='MANUAL_GYM_001')
    app.text_input(key='manual-customer-id').set_value('CUSTOM')
    submit(app)
    assert any('ya fue procesada' in e.value for e in app.error)
    assert len(bank.transactions) == 1
    assert bank.balance == balance


def test_manual_ui_real_spotify_auto_detected():
    app = submit(fill(manual_app(), 'SPOTIFY', 'SPOTIFY001'))
    bank = app.session_state['bank_state']
    subscription, = bank.subscriptions
    assert subscription.status.value == 'ACTIVE'
    assert subscription.trust_status.value == 'UNTRUSTED'
    assert not bank.subscription_candidates
    assert any('Detectamos una nueva suscripción: SPOTIFY' in s.value for s in app.success)
    assert not [b for b in app.button if b.label in LABELS]


@pytest.mark.parametrize('choice,status', list(enumerate(['CONFIRMED', 'UNSURE_BY_USER', 'REJECTED_BY_USER'])))
def test_manual_policy_confirmation_reuses_three_choices(monkeypatch, choice, status):
    # Policy/UI contract only: real-filter integration is covered separately above.
    monkeypatch.setattr(incoming, 'analyze_bank_transaction', lambda raw:
                        FilterAnalysis(True, 'SUBSCRIPTION', .82, .68, 'TEST', True, None, []))
    app = submit(fill(manual_app()))
    bank = app.session_state['bank_state']
    assert not bank.subscriptions
    assert bank.subscription_candidates[0].status.value == 'PENDING_CONFIRMATION'
    assert [b.label for b in app.button if b.label in LABELS] == LABELS
    assert 'Posible suscripción detectada' in [w.value for w in app.warning]
    balance = bank.balance
    next(b for b in app.button if b.label == LABELS[choice]).click().run()
    assert not app.exception
    assert bank.subscription_candidates[0].status.value == status
    assert bank.balance == balance
    assert len(bank.transactions) == 1


def test_manual_advanced_controls_reach_real_filter(monkeypatch):
    adapter = Mock(wraps=incoming.analyze_bank_transaction)
    monkeypatch.setattr(incoming, 'analyze_bank_transaction', adapter)
    app = fill(manual_app(), 'SERVICIO DIGITAL XYZ', 'MANUAL_ADVANCED_001')
    app.text_input(key='manual-customer-id').set_value('CUSTOM_ADVANCED')
    app.text_input(key='manual-mcc').set_value('5817')
    app.selectbox(key='manual-network').set_value('MASTERCARD')
    app.selectbox(key='manual-ecommerce').set_value(False)
    app.selectbox(key='manual-stored').set_value(False)
    app.selectbox(key='manual-present').set_value(True)
    app.selectbox(key='manual-indicator').set_value('M103')
    app.selectbox(key='manual-pos').set_value('C')
    app.selectbox(key='manual-3ds').set_value(False)
    submit(app)
    assert not app.error
    adapter.assert_called_once()
    raw = adapter.call_args.args[0]
    assert raw['merchant_id'] == 'MANUAL_ADVANCED_001'
    assert raw['customer_id'] == 'CUSTOM_ADVANCED'
    assert raw['mcc'] == '5817'
    assert raw['cit_mit_indicator'] == 'M103'
    assert raw['pos_environment'] == 'C'
    assert raw['cardholder_present'] is True
    assert raw['ecommerce'] is raw['stored_credential'] is raw['three_ds_recurring'] is False
    assert app.session_state['bank_state'].subscriptions[0].recurring_type == 'SUBSCRIPTION'
