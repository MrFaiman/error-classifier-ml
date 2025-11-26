"""
Dataset Controller
Handles dataset CRUD operations
"""
import os
import csv
from datetime import datetime
from constants import DATASET_PATH


def get_all_records():
    """
    Get all dataset records
    
    Returns:
        list: List of dataset records
    """
    records = []
    
    if not os.path.exists(DATASET_PATH):
        return records
    
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            records.append({
                'id': idx,
                'timestamp': row.get('Timestamp', ''),
                'service': row.get('Service', ''),
                'error_category': row.get('Error_Category', ''),
                'raw_input_snippet': row.get('Raw_Input_Snippet', ''),
                'root_cause': row.get('Root_Cause', '')
            })
    
    return records


def add_record(service, error_category, raw_input_snippet, root_cause=''):
    """
    Add a new record to the dataset
    
    Args:
        service: Service name
        error_category: Error category
        raw_input_snippet: Raw error message
        root_cause: Root cause description
        
    Returns:
        tuple: (success, message)
    """
    if not service or not error_category or not raw_input_snippet:
        return False, 'service, error_category, and raw_input_snippet are required'
    
    try:
        os.makedirs(os.path.dirname(DATASET_PATH), exist_ok=True)
        
        file_exists = os.path.exists(DATASET_PATH)
        
        with open(DATASET_PATH, 'a', newline='', encoding='utf-8') as f:
            fieldnames = ['Timestamp', 'Service', 'Error_Category', 'Raw_Input_Snippet', 'Root_Cause']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow({
                'Timestamp': datetime.now().isoformat(),
                'Service': service,
                'Error_Category': error_category,
                'Raw_Input_Snippet': raw_input_snippet,
                'Root_Cause': root_cause
            })
        
        return True, 'Record added successfully'
    except Exception as e:
        return False, str(e)


def update_record(record_id, service, error_category, raw_input_snippet, root_cause=''):
    """
    Update a dataset record
    
    Args:
        record_id: Record ID
        service: Service name
        error_category: Error category
        raw_input_snippet: Raw error message
        root_cause: Root cause description
        
    Returns:
        tuple: (success, message)
    """
    if not service or not error_category or not raw_input_snippet:
        return False, 'service, error_category, and raw_input_snippet are required'
    
    try:
        if not os.path.exists(DATASET_PATH):
            return False, 'Dataset not found'
        
        records = []
        with open(DATASET_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                if idx == record_id:
                    row['Service'] = service
                    row['Error_Category'] = error_category
                    row['Raw_Input_Snippet'] = raw_input_snippet
                    row['Root_Cause'] = root_cause
                records.append(row)
        
        if record_id >= len(records):
            return False, 'Record not found'
        
        with open(DATASET_PATH, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['Timestamp', 'Service', 'Error_Category', 'Raw_Input_Snippet', 'Root_Cause']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
        
        return True, 'Record updated successfully'
    except Exception as e:
        return False, str(e)


def delete_record(record_id):
    """
    Delete a dataset record
    
    Args:
        record_id: Record ID to delete
        
    Returns:
        tuple: (success, message)
    """
    try:
        if not os.path.exists(DATASET_PATH):
            return False, 'Dataset not found'
        
        records = []
        with open(DATASET_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                if idx != record_id:
                    records.append(row)
        
        with open(DATASET_PATH, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['Timestamp', 'Service', 'Error_Category', 'Raw_Input_Snippet', 'Root_Cause']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
        
        return True, 'Record deleted successfully'
    except Exception as e:
        return False, str(e)
