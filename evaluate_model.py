import json

from detector import detect_subscription
from merchant_model import MerchantRecurringModel


def safe_divide(a, b):

    if b == 0:
        return 0.0

    return a / b


def main():

    # =========================================================
    # CARGAR HISTORIAL
    # =========================================================

    with open(
        "large_historical_transactions.json",
        "r",
        encoding="utf-8"
    ) as file:

        history = json.load(file)

    # =========================================================
    # CARGAR TRANSACCIONES DE EVALUACIÓN
    # =========================================================

    with open(
        "evaluation_transactions.json",
        "r",
        encoding="utf-8"
    ) as file:

        evaluation_transactions = json.load(file)

    # =========================================================
    # CREAR MODELO DE RECURRENCIA
    # =========================================================

    merchant_model = MerchantRecurringModel(
        history
    )

    # =========================================================
    # MATRIZ DE CONFUSIÓN
    # =========================================================

    tp = 0
    fp = 0
    tn = 0
    fn = 0

    print()
    print("=" * 100)
    print("RESULTADOS DE DETECCIÓN DE RECURRENCIA")
    print("=" * 100)

    # =========================================================
    # EVALUAR CADA MERCHANT
    # =========================================================

    for tx in evaluation_transactions:

        result = detect_subscription(
            tx,
            merchant_model=merchant_model
        )

        true_type = tx["true_type"]

        # -----------------------------------------------------
        # GROUND TRUTH
        # -----------------------------------------------------
        #
        # Tanto SUBSCRIPTION como RECURRING_BILL
        # significan que habrá cobros recurrentes.
        #

        actually_recurring = (
            true_type
            in {
                "SUBSCRIPTION",
                "RECURRING_BILL"
            }
        )

        # -----------------------------------------------------
        # PREDICCIÓN
        # -----------------------------------------------------

        predicted_recurring = (
            result.is_recurring
        )

        # -----------------------------------------------------
        # MATRIZ DE CONFUSIÓN
        # -----------------------------------------------------

        if (
            actually_recurring
            and predicted_recurring
        ):

            tp += 1
            evaluation_result = "TP"

        elif (
            not actually_recurring
            and predicted_recurring
        ):

            fp += 1
            evaluation_result = "FP"

        elif (
            not actually_recurring
            and not predicted_recurring
        ):

            tn += 1
            evaluation_result = "TN"

        else:

            fn += 1
            evaluation_result = "FN"

        # -----------------------------------------------------
        # PROBABILIDAD
        # -----------------------------------------------------

        probability = (
            result.merchant_recurring_probability
        )

        if probability is None:

            probability_text = "N/A"

        else:

            probability_text = (
                f"{probability:.2%}"
            )

        # -----------------------------------------------------
        # MOSTRAR RESULTADO
        # -----------------------------------------------------

        print()

        print(
            tx["merchant"]
        )

        print(
            f"  Ground truth:      "
            f"{true_type}"
        )

        print(
            f"  Actually recurring:"
            f" {actually_recurring}"
        )

        print(
            f"  Prediction:        "
            f"{result.transaction_type}"
        )

        print(
            f"  Predicted recurring:"
            f" {predicted_recurring}"
        )

        print(
            f"  Recurring P:       "
            f"{probability_text}"
        )

        print(
            f"  Evidence:          "
            f"{result.evidence_score:.2%}"
        )

        print(
            f"  Evaluation:        "
            f"{evaluation_result}"
        )

    # =========================================================
    # MÉTRICAS
    # =========================================================

    precision = safe_divide(
        tp,
        tp + fp
    )

    recall = safe_divide(
        tp,
        tp + fn
    )

    f1 = safe_divide(
        2 * precision * recall,
        precision + recall
    )

    accuracy = safe_divide(
        tp + tn,
        tp + fp + tn + fn
    )

    # =========================================================
    # RESULTADOS
    # =========================================================

    print()
    print("=" * 100)
    print("MATRIZ DE CONFUSIÓN - RECURRENCIA")
    print("=" * 100)

    print(
        f"True Positives:  {tp}"
    )

    print(
        f"False Positives: {fp}"
    )

    print(
        f"True Negatives:  {tn}"
    )

    print(
        f"False Negatives: {fn}"
    )

    print()

    print("=" * 100)
    print("MÉTRICAS - DETECCIÓN DE RECURRENCIA")
    print("=" * 100)

    print(
        f"Precision: {precision:.2%}"
    )

    print(
        f"Recall:    {recall:.2%}"
    )

    print(
        f"F1 score:  {f1:.2%}"
    )

    print(
        f"Accuracy:  {accuracy:.2%}"
    )


if __name__ == "__main__":
    main()