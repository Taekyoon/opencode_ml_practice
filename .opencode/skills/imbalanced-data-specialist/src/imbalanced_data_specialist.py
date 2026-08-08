"""Imbalanced data specialist for semiconductor failure classification."""

import numpy as np
from sklearn.metrics import (
    auc,
    classification_report,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)

try:
    from imblearn.over_sampling import ADASYN, SMOTE
    from imblearn.under_sampling import RandomUnderSampler, TomekLinks
    from imblearn.combine import SMOTETomek
    _IMBALANCED = True
except ImportError:  # pragma: no cover
    _IMBALANCED = False


class ImbalancedDataSpecialist:
    """Analyze and fix class imbalance in binary classification data.

    Usage:
        specialist = ImbalancedDataSpecialist(random_state=42)
        ratio = specialist.analyze_imbalance(y)
        X_res, y_res = specialist.apply_sampling(X, y, method="auto")
        threshold = specialist.optimize_threshold(model, X_test, y_test, metric="f1")
        report = specialist.evaluate_imbalanced(y_true, y_pred, y_proba)
    """

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.estimators = {}
        self.last_method = None

    def analyze_imbalance(self, y, silent: bool = False):
        """Compute class distribution and recommend a sampling strategy.

        Returns the imbalance ratio (majority / minority).
        """
        import numpy as np

        unique, counts = np.unique(y, return_counts=True)
        if counts.min() == 0:
            raise ValueError("One or more classes have zero examples.")
        ratio = counts.max() / counts.min()

        if not silent:
            print("=" * 60)
            print("Class imbalance report")
            print("=" * 60)
            total = counts.sum()
            for cls, cnt in zip(unique, counts):
                print(f"  Class {cls}: {cnt} samples ({cnt / total:.1%})")
            print(f"  Imbalance ratio: {ratio:.2f}:1")
            if ratio >= 10:
                print("  -> severe imbalance, use SMOTE or SMOTETomek")
            elif ratio >= 3:
                print("  -> mild imbalance, SMOTE or TomekLinks recommended")
            else:
                print("  -> balanced enough, plain training is fine")
        return ratio

    def apply_sampling(self, X, y, method: str = "auto"):
        """Resample (X, y) with the chosen method.

        method: 'auto', 'smote', 'adasyn', 'tomek', 'random_under', 'smote_tomek'
        """
        if not _IMBALANCED:
            raise ImportError("imbalanced-learn is required. Run: pip install imbalanced-learn")

        import numpy as np

        ratios = dict(zip(*np.unique(y, return_counts=True)))
        imbalance = max(ratios.values()) / min(ratios.values())

        if method == "auto":
            if imbalance >= 10:
                method = "smote_tomek"
            elif imbalance >= 3:
                method = "smote"
            else:
                method = "tomek"

        self.sampling_method = method
        sampler = self._build_sampler(method)
        X_res, y_res = sampler.fit_resample(X, y)

        new_ratios = np.unique(y_res, return_counts=True)[1]
        print(f"[resample:{method}] {len(X)} -> {len(X_res)} (minority now {int(new_ratios.min())})")
        return X_res, y_res

    def _build_sampler(self, method):
        if method == "smote":
            return SMOTE(random_state=self.random_state)
        if method == "adasyn":
            return ADASYN(random_state=self.random_state)
        if method == "tomek":
            return TomekLinks()
        if method == "random_under":
            return RandomUnderSampler(random_state=self.random_state)
        if method == "smote_tomek":
            return SMOTETomek(random_state=self.random_state)
        raise ValueError(f"Unknown method: {method}")

    def optimize_threshold(self, model, X_val, y_val, metric: str = "f1"):
        """Find the best probability cutoff for the positive class.

        metric: 'f1' | 'recall' | 'precision'
        """
        import numpy as np

        y_proba = model.predict_proba(X_val)[:, 1]
        precision, recall, thresholds = precision_recall_curve(y_val, y_proba)

        if metric == "f1":
            # avoid div-by-zero where precision+recall == 0
            denom = precision[:-1] + recall[:-1]
            scores = np.divide(2 * precision[:-1] * recall[:-1], denom,
                               out=np.zeros_like(denom), where=denom > 0)
        elif metric == "recall":
            scores = recall[:-1]
        elif metric == "precision":
            scores = precision[:-1]
        else:
            raise ValueError(f"Unknown metric: {metric}")

        idx = int(np.argmax(scores))
        best = float(thresholds[idx])
        print(f"[threshold:{metric}] optimal cutoff = {best:.3f} (score={scores[idx]:.3f})")
        return best

    def evaluate_imbalanced(self, y_true, y_pred, y_proba=None, silent: bool = False):
        """Report imbalance-aware metrics."""
        import numpy as np

        report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)

        metrics = {
            "f1": f1,
            "precision": precision,
            "recall": recall,
            "report": report,
        }
        if y_proba is not None:
            pr_prec, pr_rec, _ = precision_recall_curve(y_true, y_proba)
            metrics["pr_auc"] = auc(pr_rec, pr_prec)
            metrics["roc_auc"] = roc_auc_score(y_true, y_proba)

        if not silent:
            print("=" * 60)
            print("Imbalance-aware evaluation")
            print("=" * 60)
            print(f"  F1         : {f1:.3f}")
            print(f"  Precision  : {precision:.3f}")
            print(f"  Recall     : {recall:.3f}")
            if "pr_auc" in metrics:
                print(f"  PR-AUC     : {metrics['pr_auc']:.3f}")
                print(f"  ROC-AUC    : {metrics['roc_auc']:.3f}")
        return metrics