import time
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_fscore_support, accuracy_score, confusion_matrix

def evaluate_detection_methods(df, ground_truth_col='ground_truth_anomaly'):
    """
    Evaluates detection performance of Z-Score, IQR, Isolation Forest, and Hybrid methods
    against ground truth labels.
    
    Computes Precision, Recall, F1-Score, Accuracy, and Confusion Matrices dynamically.
    """
    if df is None or len(df) == 0:
        return {'status': 'error', 'message': 'No data available for evaluation'}
        
    if ground_truth_col not in df.columns:
        return {'status': 'error', 'message': f"Ground truth column '{ground_truth_col}' not present in dataset"}
        
    y_true = df[ground_truth_col].astype(bool).values
    total_samples = len(y_true)
    total_true_anomalies = int(np.sum(y_true))
    
    # Method predictions dictionary
    predictions = {}
    
    # 1. Z-Score (computed_z abs > 2.5 or z_score_flag)
    if 'z_score_flag' in df.columns:
        predictions['Z-Score'] = df['z_score_flag'].astype(bool).values
    elif 'computed_z' in df.columns:
        predictions['Z-Score'] = (df['computed_z'].abs() > 2.5).values
    elif 'z_score' in df.columns:
        predictions['Z-Score'] = (df['z_score'].abs() > 2.5).values
    else:
        predictions['Z-Score'] = np.zeros(total_samples, dtype=bool)
        
    # 2. IQR
    if 'iqr_flag' in df.columns:
        predictions['IQR'] = df['iqr_flag'].astype(bool).values
    else:
        predictions['IQR'] = np.zeros(total_samples, dtype=bool)
        
    # 3. Isolation Forest
    if 'iforest_flag' in df.columns:
        predictions['Isolation Forest'] = df['iforest_flag'].astype(bool).values
    else:
        predictions['Isolation Forest'] = np.zeros(total_samples, dtype=bool)
        
    # 4. AquaGuard Hybrid (Severity != 'Normal' or risk_score >= 40)
    if 'risk_score' in df.columns:
        predictions['AquaGuard Hybrid'] = (df['risk_score'] >= 40.0).values
    elif 'severity' in df.columns:
        predictions['AquaGuard Hybrid'] = (df['severity'] != 'Normal').values
    else:
        # Fallback combination
        predictions['AquaGuard Hybrid'] = predictions['Z-Score'] | predictions['Isolation Forest']
        
    results = {}
    comparison_table = []
    
    for method_name, y_pred in predictions.items():
        # Compute confusion matrix elements
        # cm format: [[TN, FP], [FN, TP]]
        cm = confusion_matrix(y_true, y_pred, labels=[False, True])
        tn, fp, fn, tp = cm.ravel()
        
        acc = accuracy_score(y_true, y_pred)
        prec, rec, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='binary', zero_division=0)
        
        res = {
            'method': method_name,
            'precision': round(float(prec) * 100.0, 1),
            'recall': round(float(rec) * 100.0, 1),
            'f1_score': round(float(f1) * 100.0, 1),
            'accuracy': round(float(acc) * 100.0, 1),
            'true_positives': int(tp),
            'false_positives': int(fp),
            'true_negatives': int(tn),
            'false_negatives': int(fn),
            'detected_anomalies': int(tp + fp)
        }
        results[method_name] = res
        comparison_table.append(res)
        
    # Sort comparison table by F1-Score descending
    comparison_table.sort(key=lambda x: x['f1_score'], reverse=True)
    
    return {
        'status': 'success',
        'dataset_summary': {
            'total_samples': total_samples,
            'ground_truth_anomalies': total_true_anomalies,
            'ground_truth_rate_pct': round((total_true_anomalies / max(total_samples, 1)) * 100.0, 2)
        },
        'comparison_table': comparison_table,
        'details': results
    }
