import unittest

from hospitality_ai.linear_model import (
    FEATURE_NAMES,
    encode_features,
    evaluate_linear_model,
    fit_linear_model,
)
from hospitality_ai.synthetic_data import generate_records


class LinearModelTests(unittest.TestCase):
    def test_target_and_anomaly_label_are_not_features(self) -> None:
        record = generate_records(1, seed=2)[0]
        features = encode_features(record)
        self.assertEqual(len(features), len(FEATURE_NAMES))
        self.assertNotIn("electricity_kwh", FEATURE_NAMES)
        self.assertNotIn("is_injected_anomaly", FEATURE_NAMES)
        self.assertIn("day_is_saturday", FEATURE_NAMES)

    def test_model_beats_mean_baseline(self) -> None:
        _, result = evaluate_linear_model(generate_records(1_000, seed=2026), seed=2026)
        self.assertLess(result.model_mae_kwh, result.baseline_mae_kwh)
        self.assertGreater(result.mae_improvement_pct, 50.0)

    def test_learned_customer_effect_is_positive(self) -> None:
        model = fit_linear_model(generate_records(1_000, seed=12))
        customer_index = FEATURE_NAMES.index("customers")
        self.assertGreater(model.coefficients[customer_index], 0)


if __name__ == "__main__":
    unittest.main()
