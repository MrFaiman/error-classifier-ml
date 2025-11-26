"""
Quiz Controller
Generates quiz questions about error classifications
"""
import random
import os
import glob
from constants import DOCS_ROOT_DIR


def _get_all_error_categories():
    """Get all available error categories from documentation files"""
    pattern = os.path.join(DOCS_ROOT_DIR, '**', '*.md')
    files = glob.glob(pattern, recursive=True)
    
    categories = []
    for filepath in files:
        parts = filepath.replace('\\', '/').split('/')
        try:
            services_idx = parts.index('services')
            if services_idx + 2 < len(parts):
                service = parts[services_idx + 1]
                category = parts[services_idx + 2].replace('.md', '')
                
                # Read description from file
                description = ""
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Extract description section
                        lines = content.split('\n')
                        in_description = False
                        for line in lines:
                            if line.strip().startswith('## Description'):
                                in_description = True
                            elif line.strip().startswith('##') and in_description:
                                break
                            elif in_description and line.strip():
                                description += line.strip() + " "
                except:
                    pass
                
                categories.append({
                    'service': service,
                    'category': category,
                    'description': description.strip(),
                    'file_path': filepath
                })
        except (ValueError, IndexError):
            continue
    
    return categories


def _generate_error_scenario(category_info):
    """Generate a realistic error scenario for a category"""
    category = category_info['category']
    service = category_info['service']
    
    # Map categories to realistic error scenarios
    scenarios = {
        'NEGATIVE_VALUE': [
            "Quantity field contains value: -5",
            "Price is set to -10.50",
            "Weight measurement shows -2.3 kg",
            "Temperature reading is -999"
        ],
        'MISSING_FIELD': [
            "API request missing 'timestamp' field",
            "Required field 'user_id' not provided",
            "Sensor data lacks 'location' parameter",
            "Missing mandatory 'status' field"
        ],
        'SCHEMA_VALIDATION': [
            "Data format does not match expected schema",
            "Invalid JSON structure in request body",
            "Field type mismatch: expected number, got string",
            "Schema validation failed for payload"
        ],
        'GEO_OUT_OF_BOUNDS': [
            "Latitude value 95.5 exceeds valid range",
            "Longitude -200.0 is outside boundaries",
            "GPS coordinates (91, 181) are invalid",
            "Geographic location out of service area"
        ],
        'REGEX_MISMATCH': [
            "Input 'abc123' does not match pattern '^[0-9]+$'",
            "Email format validation failed",
            "Phone number format is incorrect",
            "String pattern does not match regex"
        ],
        'SECURITY_ALERT': [
            "Unauthorized access attempt detected",
            "SQL injection pattern identified in input",
            "Suspicious activity from IP address",
            "Authentication token has been compromised"
        ]
    }
    
    # Get scenario or create generic one
    if category in scenarios:
        return random.choice(scenarios[category])
    else:
        return f"Error detected in {service}: {category.replace('_', ' ').lower()}"


def generate_quiz_question():
    """
    Generate a single quiz question with 4 options
    
    Returns:
        dict with question, options (A-D), correct_answer, and explanation
    """
    categories = _get_all_error_categories()
    
    if len(categories) < 4:
        return None
    
    # Select correct answer
    correct_category = random.choice(categories)
    
    # Select 3 wrong answers from different services if possible
    wrong_categories = [cat for cat in categories if cat != correct_category]
    
    # Try to get diverse wrong answers
    wrong_answers = []
    services_used = {correct_category['service']}
    
    # First pass: try to get from different services
    for cat in wrong_categories:
        if cat['service'] not in services_used and len(wrong_answers) < 3:
            wrong_answers.append(cat)
            services_used.add(cat['service'])
    
    # Second pass: fill remaining slots
    for cat in wrong_categories:
        if cat not in wrong_answers and len(wrong_answers) < 3:
            wrong_answers.append(cat)
    
    # If still not enough, just take random ones
    while len(wrong_answers) < 3 and wrong_categories:
        cat = random.choice(wrong_categories)
        if cat not in wrong_answers:
            wrong_answers.append(cat)
    
    # Generate error scenario
    error_scenario = _generate_error_scenario(correct_category)
    
    # Create options
    all_options = [correct_category] + wrong_answers
    random.shuffle(all_options)
    
    # Find correct answer letter
    correct_letter = 'ABCD'[all_options.index(correct_category)]
    
    # Build question
    question = {
        'question': f"What error category does this belong to?\n\n\"{error_scenario}\"",
        'options': {
            'A': f"{all_options[0]['category']} ({all_options[0]['service']})",
            'B': f"{all_options[1]['category']} ({all_options[1]['service']})",
            'C': f"{all_options[2]['category']} ({all_options[2]['service']})",
            'D': f"{all_options[3]['category']} ({all_options[3]['service']})"
        },
        'correct_answer': correct_letter,
        'explanation': f"This error indicates {correct_category['category'].replace('_', ' ').lower()} in the {correct_category['service']} service. {correct_category['description'][:200] if correct_category['description'] else 'See documentation for more details.'}",
        'service': correct_category['service'],
        'category': correct_category['category']
    }
    
    return question


def generate_quiz(num_questions=10):
    """
    Generate a full quiz with multiple questions
    
    Args:
        num_questions: Number of questions to generate
        
    Returns:
        List of question dictionaries
    """
    questions = []
    categories_used = set()
    
    for _ in range(num_questions):
        question = generate_quiz_question()
        if question:
            # Try to avoid repeating the same category as correct answer
            category_key = f"{question['service']}-{question['category']}"
            attempts = 0
            while category_key in categories_used and attempts < 5:
                question = generate_quiz_question()
                if question:
                    category_key = f"{question['service']}-{question['category']}"
                attempts += 1
            
            categories_used.add(category_key)
            questions.append(question)
    
    return questions


def check_answer(question_data, user_answer):
    """
    Check if the user's answer is correct
    
    Args:
        question_data: The original question dictionary
        user_answer: User's answer (A, B, C, or D)
        
    Returns:
        dict with is_correct, correct_answer, and explanation
    """
    is_correct = user_answer.upper() == question_data['correct_answer']
    
    return {
        'is_correct': is_correct,
        'correct_answer': question_data['correct_answer'],
        'user_answer': user_answer.upper(),
        'explanation': question_data['explanation']
    }
