import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from models import setup_db, Question, Category
from flask_cors import CORS

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    questions = [question.format() for question in selection]
    current_questions = questions[start:end]
    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    cors = CORS(app)
    # cors = CORS(app, resources=
    # {"r*/api/*": {"origins": "*"}},send_wildcard=True )
    # CORS Headers

    @app.after_request
    def after_request(response):
        # Set up CORS. Allow '*' for origins.
        # response.headers.add('Access-Control-Allow-Origin',
        # 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    '''
    Create a GET endpoint to get questions based on category.
    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    '''
    @app.route('/categories')
    def retrieve_categories():
        categories = Category.query.order_by(Category.id).all()
        c_dict = {}  # frontend requires dictionary type. see FormView.js
        for category in categories:
            c_dict[category.id] = category.type
        if len(categories) == 0:
            abort(404)
        return jsonify({
          'success': True,
          'categories': c_dict,
        })
    '''
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.
    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination
    at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    '''
    @app.route('/questions')
    def retrieve_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)
        if len(current_questions) == 0:
            abort(404)
        categories = Category.query.all()
        c_dict = {}
        for category in categories:
            c_dict[category.id] = category.type
    # result: {1: 'Science', 2: 'Art', 3: 'Geography',
    # 4: 'History', 5: 'Entertainment', 6: 'Sports'}
    # if I code as below, it will not match the frontend...
    # and will get many errors from frontend.
    # for category in categories:
    #   c_dict=dict(c_dict,**category.format())
    # result {'id': 6, 'type': 'Sports'}
        return jsonify({
            'success': True,
            'questions': current_questions,
            'categories': c_dict,
            # QuestionView.js sets the type as dictionary type. categories: {},
            # if I send a wrong type of data, I will get an error blow.
            # Access to XMLHttpRequest
            # at 'http://127.0.0.1:5000/questions?page=1'
            # from origin 'http://localhost:3000'
            # has been blocked by CORS policy:
            # No 'Access-Control-Allow-Origin' header
            # is present on the requested resource.
            'total_questions': len(Question.query.all())
        })
    '''
    Create an endpoint to DELETE question using a question ID.
    TEST: When you click the trash icon next to a question,
    the question will be removed.
    This removal will persist in the database and when you refresh the page.
    '''
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id)
            question = question.one_or_none()
            if question is None:
                abort(404)
                # wendy: it will handle 404 as an exception.
                # abort 422, not 404.so 404 has symbolic meaning here.
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
    '''
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.
    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question
    will appear at the end of the last page
    of the questions list in the "List" tab.
    '''
    '''
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.
    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    '''
    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()
        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)
        search = body.get('searchTerm', None)
        try:
            if search:
                selection = Question.query.order_by(Question.id).filter(
                                    Question.question.like(
                                        '%{}%'.format(search))).all()
                current_questions = paginate_questions(request, selection)
                return jsonify({
                    'success': True,
                    'questions': current_questions,
                    'total_questions': len(selection)
                })
            else:
                # for testing None creation.
                if (new_question is None)or(new_answer is None)or(
                      new_category is None)or(new_difficulty is None):
                    abort(422)
                question = Question(question=new_question, answer=new_answer,
                                    category=new_category,
                                    difficulty=new_difficulty)
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

    # match with frontend/src/components/QuestionView.js
    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def retrieve_questions_by_category(category_id):
        try:
            ids = []
            categories = Category.query.with_entities(Category.id).all()
            # print(categories)# result [(1,), (2,), (3,), (4,), (5,), (6,)]
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
    '''
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.
    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    '''
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
