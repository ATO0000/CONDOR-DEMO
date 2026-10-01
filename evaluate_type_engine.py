import json

from detector import detect_subscription
from merchant_model import MerchantRecurringModel
from type_engine import classify_recurring_type


def main():

    # =========================================================
    # CARGAR DATASETS
    # =========================================================

    with open(
        "large_historical_transactions.json",
        "r",
        encoding="utf-8"
    ) as file:

        history = json.load(file)

    with open(
        "evaluation_transactions.json",
        "r",
        encoding="utf-8"
    ) as file:

        evaluation = json.load(file)

    # =========================================================
    # MODELO DE RECURRENCIA
    # =========================================================

    recurring_model = MerchantRecurringModel(
        history
    )

    correct = 0
    incorrect = 0
    unknown = 0
    skipped = 0

    print()
    print("=" * 100)
    print("TYPE ENGINE EVALUATION")
    print("=" * 100)

    # =========================================================
    # EVALUACIÓN
    # =========================================================

    for tx in evaluation:

        # -----------------------------------------------------
        # ETAPA 1: DETECTAR RECURRENCIA
        # -----------------------------------------------------

        recurrence_result = detect_subscription(
            tx,
            merchant_model=recurring_model
        )

        # Si no parece recurrente, el Type Engine
        # no debería intervenir.
        if not recurrence_result.is_recurring:

            skipped += 1

            print()
            print(tx["merchant"])
            print(
                f"  MCC:         "
                f"{tx.get('mcc', 'N/A')}"
            )
            print(
                f"  Ground truth:"
                f" {tx['true_type']}"
            )
            print(
                "  Type Engine: SKIPPED "
                "(not recurring)"
            )

            continue

        # -----------------------------------------------------
        # OBTENER FEATURES HISTÓRICAS
        # -----------------------------------------------------

        merchant_analysis = (
            recurring_model.predict(
                tx["merchant_id"]
            )
        )

        features = merchant_analysis.get(
            "features"
        )

        # -----------------------------------------------------
        # ETAPA 2: CLASIFICAR TIPO
        # -----------------------------------------------------

        type_result = classify_recurring_type(
            tx,
            merchant_features=features
        )

        true_type = tx["true_type"]

        predicted_type = (
            type_result.recurring_type
        )

        # -----------------------------------------------------
        # EVALUACIÓN
        # -----------------------------------------------------

        if predicted_type == true_type:

            correct += 1
            evaluation_result = "CORRECT"

        elif predicted_type == "UNKNOWN_RECURRING":

            unknown += 1
            evaluation_result = "UNKNOWN"

        else:

            incorrect += 1
            evaluation_result = "INCORRECT"

        # -----------------------------------------------------
        # MOSTRAR RESULTADO
        # -----------------------------------------------------

        print()
        print(tx["merchant"])

        print(
            f"  MCC:          "
            f"{tx.get('mcc', 'N/A')}"
        )

        print(
            f"  Ground truth: "
            f"{true_type}"
        )

        print(
            f"  Prediction:   "
            f"{predicted_type}"
        )

        print(
            f"  Confidence:   "
            f"{type_result.confidence:.2%}"
        )

        print(
            f"  Evaluation:   "
            f"{evaluation_result}"
        )

        print("  Reasons:")

        for reason in type_result.reasons:

            print(
                f"    - {reason}"
            )

    # =========================================================
    # RESUMEN
    # =========================================================

    classified_total = (
        correct
        + incorrect
        + unknown
    )

    print()
    print("=" * 100)
    print("TYPE ENGINE SUMMARY")
    print("=" * 100)

    print(
        f"Correct:   {correct}"
    )

    print(
        f"Incorrect: {incorrect}"
    )

    print(
        f"Unknown:   {unknown}"
    )

    print(
        f"Skipped:   {skipped}"
    )

    if classified_total > 0:

        accuracy = (
            correct
            / classified_total
        )

        print(
            f"Accuracy:  "
            f"{accuracy:.2%}"
        )


if __name__ == "__main__":
    main()