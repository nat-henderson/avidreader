from flask import Flask, render_template, request
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required

from genprotos.protos_pb2 import QuizProto

# Create app
app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'super-secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tmp.db'

# Create database connection object
db = SQLAlchemy(app)

# Define models
roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

class Book(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(255))
    author_id = db.Column(db.Integer(), db.ForeignKey('author.id'))

class Author(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    books = db.relationship('Book', backref="author")
    name = db.String(255)

class Quiz(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    book_id = db.Column(db.Integer(), db.ForeignKey('book.id'))
    book = db.relationship('Book', backref="quizzes")
    # a QuizProto
    quiz = db.Column(db.LargeBinary())

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# Create a user to test with
@app.before_first_request
def create_user():
    db.drop_all()
    db.create_all()
    user_datastore.create_user(email='nath@nmckinley.com', password='password')
    db.session.commit()

@app.route('/api/newbook')
def create_book():
    book = Book()
    book.title = request.form.get('title')
    book.author_id = request.form.get('author')
    db.session.add(book)
    db.session.commit()
    return ''

@app.route('/api/newauthor')
def create_author():
    author = Author()
    author.name = request.form.get('name')
    db.session.add(author)
    db.session.commit()
    return ''

@app.route('/api/newquiz')
def create_quiz():
    quiz = Quiz()
    quiz.book_id = request.form.get('book_id')
    quizproto = QuizProto()
    for question in json.loads(request.form.get('quiz')):
        questionproto = quizproto.question.add()
        questionproto.question = question['question']
        for idx, answer in enumerate(question['answers']):
            answerproto = questionproto.answer.add()
            answerproto.answer = answer
            answerproto.is_correct = idx == question['correct_answer']
    quiz.quiz = quizproto.SerializeToString()
    db.session.add(quiz)
    db.session.commit()
    return ''

# Views
@app.route('/')
@login_required
def home():
    return render_template('index.tmpl')

if __name__ == '__main__':
    app.run()
