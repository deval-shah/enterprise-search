import pandas as pd
import json
import numpy as np
from datetime import datetime
import os
import argparse
import matplotlib.pyplot as plt


def read_json(file_path):
    """Read JSON file and return the data."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def analyse(data):
    """Extract and organize metrics data."""
    metrics_sum = {
        "ContextualPrecisionMetric": [],
        "ContextualRecallMetric": [],
        "FaithfulnessMetric": [],
        "AnswerRelevancyMetric": [],
        "ContextualRelevancyMetric": [],
        "Coherence": []
    }

    for result in data:
        metrics = result.get('metrics', [])
        for metric in metrics:
            if metric is None:
                continue
            name = metric.get('name')
            score = metric.get('score', 0)
            if name in metrics_sum:
                metrics_sum[name].append(score)
    return metrics_sum

def calc_mean(metric_data):
    """Calculate mean for each metric."""
    return {metric: np.mean(scores) for metric, scores in metric_data.items()}

def calc_std_deviation(metric_data):
    """Calculate standard deviation for each metric."""
    return {metric: np.std(scores) for metric, scores in metric_data.items()}

def calc_median(metric_data):
    """Calculate median for each metric."""
    return {metric: np.median(scores) for metric, scores in metric_data.items()}

def save_to_csv(metric_data, model_used, side_note, file_path="eval_metrics.csv"):
    """Save evaluation metrics to CSV with additional metadata."""
    df = pd.DataFrame(metric_data)
    # Add a timestamp, model used, and side note to identify each run
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df["Run Timestamp"] = timestamp
    df["Model Used"] = model_used
    df["Side Note"] = side_note
    
    if os.path.exists(file_path):  
        existing_df = pd.read_csv(file_path)        
        df = pd.concat([existing_df, df], ignore_index=True)
        df.to_csv(file_path, mode='w', header=True, index=False)
    else:
        df.to_csv(file_path, mode='w', header=True, index=False)
    save_plot(df)
    print(f"Metrics saved to {file_path}")

def save_plot(df, plot_file="metrics_plot.png"):
    """Save plot of evaluation metrics."""
    plt.figure(figsize=(10, 6))
    timestamps = df['Run Timestamp'].unique()
    bar_width = 0.35
    positions = range(len(df['Metric'].unique()))
    for i, timestamp in enumerate(timestamps):
        df_filtered = df[df['Run Timestamp'] == timestamp]
        plt.bar([p + bar_width * i for p in positions], df_filtered['Mean'], 
                width=bar_width, label=f'Timestamp: {timestamp}')


    plt.xlabel('Metrics')
    plt.ylabel('Mean Value')
    plt.title('Model Performance Evaluation by Timestamps')
    plt.xticks([p + bar_width for p in positions], df['Metric'].unique(), rotation=45)

    # Display legend and plot
    plt.legend(title='Run Timestamp')
    plt.tight_layout()
    # Save the figure
    plt.savefig(plot_file)
    print(f"Plot saved to {plot_file}")
    # Optionally, display the plot
    plt.show()



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Evaluate model performance and save metrics.')
    
    parser.add_argument('--json_file', type=str, required=True, 
                        help='Path to the JSON file containing evaluation results')
    parser.add_argument('--model_used', type=str, required=True, 
                        help='Name of the model used for the evaluation run')
    parser.add_argument('--side_note', type=str, required=False, default="", 
                        help='Any additional notes regarding the evaluation run')
    parser.add_argument('--output_file', type=str, default="eval_metrics.csv", 
                        help='Output CSV file to save the evaluation metrics')

    args = parser.parse_args()
    data = read_json(args.json_file)
    metric_data = analyse(data)

    mean_metric = calc_mean(metric_data)
    median_metric = calc_median(metric_data)
    std_metric = calc_std_deviation(metric_data)
    combined_metrics = {
        "Metric": list(mean_metric.keys()),
        "Mean": list(mean_metric.values()),
        "Median": list(median_metric.values()),
        "Standard Deviation": list(std_metric.values())
    }
    save_to_csv(combined_metrics, args.model_used, args.side_note, file_path=args.output_file)
