import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
#import randomy
from models import setup_db, Question, Category
#wendy--cors setting
from flask_cors import CORS

QUESTIONS_PER_PAGE = 10
def paginate_questions(request, selection):
  page = request.args.get('page', 1, type=int)
  start =  (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [question.format() for question in selection]
  current_questions = questions[start:end]
  return current_questions
def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  cors = CORS(app)
#  cors = CORS(app, resources={"r*/api/*": {"origins": "*"}},send_wildcard=True )
# CORS Headers 
  @app.after_request
  def after_request(response):
#    response.headers.add('Access-Control-Allow-Origin','http://localhost:3000')
    response.headers.add('Access-Control-Allow-Origin','*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

  @app.route('/categories')
  def retrieve_categories():
    categories = Category.query.order_by(Category.id).all()
    c_dict={} #frontend requires dictionary type. see FormView.js
    for category in categories:
        c_dict[category.id] = category.type
    if len(categories) == 0:
      abort(404)
    return jsonify({
      'success': True,
      'categories': c_dict,
    })

  @app.route('/questions')
  def retrieve_questions():
    selection = Question.query.order_by(Question.id).all()
    current_questions = paginate_questions(request, selection)

    if len(current_questions) == 0:
      abort(404)
    categories = Category.query.all()
    c_dict={}
    for category in categories:
        c_dict[category.id] = category.type
    #result: {1: 'Science', 2: 'Art', 3: 'Geography', 4: 'History', 5: 'Entertainment', 6: 'Sports'}
    #if I code as below, it will not match the frontend...
      # for category in categories:
      #   c_dict=dict(c_dict,**category.format()) #result {'id': 6, 'type': 'Sports'}

    return jsonify({
      'success': True,
      'questions': current_questions,
      'categories':c_dict, #QuestionView.js sets the type as dictionary type. categories: {},
      #if I send a wrong type of data, I will get an error blow.
        #Access to XMLHttpRequest at 'http://127.0.0.1:5000/questions?page=1' 
        # from origin 'http://localhost:3000' has been blocked by CORS policy: 
        # No 'Access-Control-Allow-Origin' header is present on the requested resource.
#      'currentCategory':categories_dict
      'total_questions': len(Question.query.all())
    })

  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    try:
      question = Question.query.filter(Question.id == question_id).one_or_none()
      if question is None:
        abort(404) # wendy: it will handle 404 as an exception. abort 422, not 404.so, how to fix it?
      question.delete()
      selection = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, selection)

      return jsonify({
          'success': True,
          'deleted': question_id,
          'questions': current_questions,
          'total_questions': len(Question.query.all())
        })
    except:
      abort(422)

  @app.route('/questions', methods=['POST'])
  def create_question():
    body = request.get_json()
    new_question = body.get('question', None)
    new_answer = body.get('answer', None)
    new_category = body.get('category', None)
    new_difficulty = body.get('difficulty', None)
    search = body.get('searchTerm',None)

    try:
      if search:
        selection = Question.query.order_by(Question.id).filter(Question.question.like('%{}%'.format(search))).all()
        current_questions = paginate_questions(request, selection)
        return jsonify({
          'success': True,
          'questions': current_questions,
          'total_questions': len(selection)
        })
      else:
        if (new_question is None)or(new_answer is None)or(new_category is None)or(new_difficulty is None):
          abort(422)
        question = Question(question=new_question, answer=new_answer, category=new_category,difficulty=new_difficulty)
        question.insert()
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)
        return jsonify({
          'success': True,
          'created': question.id,
          'questions': current_questions,
          'question_created': question.question,
          'total_questions': len(Question.query.all())
        })

    except:
      abort(422)

  @app.route('/categories/<int:category_id>/questions', methods=['GET'])
  def retrieve_questions_by_category(category_id):
    try:
        ids = []
        categories = Category.query.with_entities(Category.id).all()
        # print("-----------debug----------------")
        # print(categories)#[(1,), (2,), (3,), (4,), (5,), (6,)]
        for (id,) in categories:
            ids.append(id)
        if category_id not in ids:
            abort(404)
        questions = Question.query.filter(
                    Question.category == str(category_id)).all()
        return jsonify({
            'success': True,
            'questions': [question.format() for question in questions],
            'total_question': len(questions),
            'current_category': category_id
        })
    except:
        abort(404)

  # This is a POST endpoint to get questions to play the quiz
  @app.route('/quizzes', methods=['POST'])
  def play_quiz():
    body = request.get_json()
    previousQuestions = body.get('previous_questions')
    quiz_category = body.get('quiz_category')
    if quiz_category is None:
        abort(400)
    questions = None
    id = (quiz_category['id'])
    if id != 0:
        questions = Question.query.filter(
                    Question.category == str(id)).all()
    else:
        questions = Question.query.all()
    if previousQuestions is not None:
        for question in questions:
            if question.id not in previousQuestions:
                return jsonify({
                    'success': True,
                    'question': question.format()
                })
    else:
        return jsonify({
            "success": True,
            'question': questions[0].format()
        })

  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      "success": False, 
      "error": 404,
      "message": "resource not found"
      }), 404

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      "success": False, 
      "error": 422,
      "message": "unprocessable"
      }), 422

  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      "success": False, 
      "error": 400,
      "message": "bad request"
      }), 400
    
  return app

    