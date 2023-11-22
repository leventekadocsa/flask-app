from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'site.db')
db = SQLAlchemy(app)


# Define User model (you may need additional fields)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

# Define Post model (you may need additional fields)
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False) 
    content = db.Column(db.String(140), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Add a new route to handle post creation
@app.route('/create_post', methods=['POST'])
@login_required
def create_post():
    title = request.form['title']
    content = request.form['content']
    new_post = Post(title=title, content=content, user_id=current_user.id)
    db.session.add(new_post)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    # Check if the user is the author of the post
    if current_user.id == post.user_id:
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted successfully!', 'success')
    else:
        flash('You are not authorized to delete this post.', 'danger')

    return redirect(url_for('home'))


# Define Message model (you may need additional fields)
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(140), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@app.route('/messages')
@login_required
def messages():
    users = User.query.all()
    posts = Post.query.all()
    messages = Message.query.filter(Message.receiver_id == current_user.id)
    return render_template('messages.html', messages=messages, users=users, posts=posts)


# Add a new route to handle sending messages
@app.route('/send_message/<int:user_id>', methods=['POST'])
@login_required
def send_message(user_id):
    content = request.form['message_content']
    sender_id = current_user.id
    new_message = Message(content=content, sender_id=sender_id, receiver_id=user_id)
    db.session.add(new_message)
    db.session.commit()
    return redirect(url_for('home'))

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Define routes for your application
@app.route('/home')
@login_required
def home():
    users = User.query.all()  # Retrieve all users from the database
    posts = Post.query.all()
    return render_template('home.html', posts=posts, users=users)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username already exists in the database
        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash('Username already in use. Please choose a different username.', 'warning')
            return redirect(url_for('register', message='Username already in use'))

        # If the username is not in use, add the new user to the database
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully. You can now log in.', 'success')
        return redirect(url_for('login'))

    # Pass the flash message to the template
    message = request.args.get('message', None)
    return render_template('register.html', message=message)


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    if request.method == 'POST':
        logout_user()
        return redirect(url_for('login'))
    return redirect(url_for('login'))  # This handles GET requests

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    posts = Post.query.all()
    return render_template('search.html', posts=posts)

@app.route('/about')
@login_required
def about():
    return render_template('about.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
