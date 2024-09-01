
import pandas as pd
import json

def gather_result(data):
    result_metrics = {}
    
    for entry in data:
        metrics = entry.get('metrics', [])
        for metric in metrics:
            if metric:
                metric_name = metric.get('name')
                if metric_name:
                    result_metrics[metric_name] = result_metrics.get(metric_name, 0) + metric.get('score', 0)

    average_metrics = {metric: result_metrics[metric] / len(data) for metric in result_metrics}
    print(average_metrics)
if __name__ == "__main__":
    with open('./results/eval_20240901_194542.json', 'r') as file:
        data = json.load(file)
        gather_result(data)