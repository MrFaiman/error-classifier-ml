"""
Quiz Routes
Endpoints for quiz/exam mode
"""
from flask import Blueprint, request, jsonify
from api.controllers import quiz_controller

bp = Blueprint('quiz', __name__, url_prefix='/api')


@bp.route('/quiz/generate', methods=['GET'])
def generate_quiz():
    """Generate a new quiz with multiple questions"""
    try:
        num_questions = request.args.get('num_questions', 10, type=int)
        
        # Limit to reasonable range
        num_questions = max(1, min(num_questions, 50))
        
        questions = quiz_controller.generate_quiz(num_questions)
        
        if not questions:
            return jsonify({'error': 'Not enough error categories to generate quiz'}), 400
        
        return jsonify({
            'questions': questions,
            'total': len(questions)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/quiz/question', methods=['GET'])
def get_single_question():
    """Get a single quiz question"""
    try:
        question = quiz_controller.generate_quiz_question()
        
        if not question:
            return jsonify({'error': 'Not enough error categories to generate question'}), 400
        
        return jsonify(question)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/quiz/check', methods=['POST'])
def check_answer():
    """Check if an answer is correct"""
    try:
        data = request.json
        question_data = data.get('question')
        user_answer = data.get('answer')
        
        if not question_data or not user_answer:
            return jsonify({'error': 'question and answer are required'}), 400
        
        result = quiz_controller.check_answer(question_data, user_answer)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
