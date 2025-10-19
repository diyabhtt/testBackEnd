"""
Export latest analysis data for Alexa skill consumption.
"""
import json
import os
from datetime import datetime

def export_to_json(latest_analysis: dict, output_file: str = "latest_analysis.json"):
    """
    Export current analysis to JSON file.
    Alexa Lambda can read this from S3 or local storage.
    """
    export_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "symbols": latest_analysis
    }
    
    filepath = os.path.join(os.path.dirname(__file__), output_file)
    with open(filepath, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"📤 Exported analysis to {filepath}")
    return filepath

def export_to_dynamodb(latest_analysis: dict, table_name: str = "FinGalaxyAnalysis"):
    """
    Optional: Export to DynamoDB for Alexa Lambda to consume.
    Requires: pip install boto3
    """
    try:
        import boto3
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)
        
        for symbol, data in latest_analysis.items():
            table.put_item(Item={
                'symbol': symbol,
                'timestamp': datetime.utcnow().isoformat(),
                **data
            })
        
        print(f"📤 Exported to DynamoDB table: {table_name}")
    except ImportError:
        print("⚠️  boto3 not installed. Skipping DynamoDB export.")
    except Exception as e:
        print(f"❌ DynamoDB export error: {e}")
