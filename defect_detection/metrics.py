"""Category-level ranking metrics. Undefined single-class values are null."""
import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score


def ranking_metrics(labels, scores):
    labels, scores = np.asarray(labels), np.asarray(scores)
    if labels.shape != scores.shape or not labels.size or not np.isin(labels, [0, 1]).all() or not np.isfinite(scores).all():
        raise ValueError('Expected equal nonempty shapes, binary labels, finite scores')
    labels, scores = labels.ravel(), scores.ravel()
    both = np.unique(labels).size == 2
    return {'auroc': float(roc_auc_score(labels, scores)) if both else None,
            'average_precision': float(average_precision_score(labels, scores)) if both else None,
            'positive_prevalence': float(labels.mean()), 'count': int(labels.size),
            'undefined_reason': None if both else 'single_class'}


def normal_threshold(scores):
    values = np.asarray(scores)
    if not values.size or not np.isfinite(values).all():
        raise ValueError('Calibration scores must be nonempty and finite')
    return float(np.quantile(values, .95, method='higher'))
