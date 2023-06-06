import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database_file.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

migrate = Migrate(app, db)



# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


class Prompt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('prompts', lazy=True))
    category = db.relationship('Category', backref=db.backref('prompts', lazy=True))

    likes = db.relationship('User', secondary='prompt_likes', backref=db.backref('liked_prompts', lazy=True))


prompt_likes = db.Table('prompt_likes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('prompt_id', db.Integer, db.ForeignKey('prompt.id'), primary_key=True)
)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return self.name


# Routes
@app.route('/')
def home():
    prompts = Prompt.query.all()
    return render_template('home.html', prompts=prompts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            session['user_id'] = user.id
            return redirect(url_for('home'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/create_prompt', methods=['GET', 'POST'])
def create_prompt():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        content = request.form['content']
        category_id = request.form['category']
        user_id = session['user_id']
        prompt = Prompt(content=content, user_id=user_id, category_id=category_id)
        db.session.add(prompt)
        db.session.commit()
        return redirect(url_for('home'))

    categories = Category.query.all()
    return render_template('create_prompt.html', categories=categories)


@app.route('/edit_prompt/<int:prompt_id>', methods=['GET', 'POST'])
def edit_prompt(prompt_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    prompt = Prompt.query.get_or_404(prompt_id)
    if prompt.user_id != session['user_id']:
        return redirect(url_for('home'))

    if request.method == 'POST':
        prompt.content = request.form['content']
        prompt.category_id = request.form['category']
        db.session.commit()
        return redirect(url_for('home'))

    categories = Category.query.all()
    return render_template('edit_prompt.html', prompt=prompt, categories=categories)


@app.route('/delete_prompt/<int:prompt_id>')
def delete_prompt(prompt_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    prompt = Prompt.query.get_or_404(prompt_id)
    if prompt.user_id != session['user_id']:
        return redirect(url_for('home'))

    db.session.delete(prompt)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/like_prompt/<int:prompt_id>')
def like_prompt(prompt_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    prompt = Prompt.query.get_or_404(prompt_id)
    user = User.query.get(user_id)

    if user in prompt.likes:
        prompt.likes.remove(user)
    else:
        prompt.likes.append(user)

    db.session.commit()

    return redirect(url_for('home'))





if __name__ == '__main__':
    # Create the database tables
    with app.app_context():
        db.create_all()

        # Create prompt categories
        # categories = [
        #     Category(name='SEO'),
        #     Category(name='Programming'),
        #     Category(name='Chrome Extensions'),
        #     Category(name='Flutter'),
        #     Category(name='Story')
        # ]

        # db.session.bulk_save_objects(categories)
        # db.session.commit()

    app.run(debug=True)
