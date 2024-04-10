from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from backend.models import db, User, Profile
from dotenv import load_dotenv
from backend.services import login, get_profile, update_profile, register
import os
from werkzeug.security import generate_password_hash
from flask_migrate import Migrate

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Get the database URL from the environment variable
database_url = os.environ.get('CLEARDB_DATABASE_URL').replace('mysql://', 'mysql+pymysql://')

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure SQLAlchemy engine options
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 299,  # Adjust with your requirements
    'pool_pre_ping': True
}

db.init_app(app)
migrate = Migrate(app, db)

# Configure CORS. This allows all origins. For development only!
CORS(app, support_credentials=True)

@app.cli.command('create_tables')
def create_tables():
    """Create database tables from SQLAlchemy models."""
    db.create_all()
    print('Tables created.')


@app.route('/')
def home():
    return 'Welcome to the Flask App!'


@app.route('/login', methods=['GET', 'POST', 'OPTIONS'])
@cross_origin(supports_credentials=True)
def login_route():
    if request.method == 'POST':
        username = request.json['username']
        password = request.json['password']
        user, status_code = login(username, password)
        if user:
            return jsonify({"user_id": user['user_id']}), 200
        else:
            return jsonify({"message": "Invalid username or password"}), status_code
    elif request.method == 'GET':
        return jsonify({"message": "GET method is not supported for /login."}), 405
    else:
        return '', 204


@app.route('/register', methods=['POST', 'GET'])
@cross_origin()
def register_route():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        bio = data.get('bio')  # Extract bio data from the request
        response, status_code = register(username, password, email, bio)
        return jsonify(response), status_code
    elif request.method == 'GET':
        return jsonify({"message": "GET method for registration is not supported."}), 405


@app.route('/profile/<int:user_id>', methods=['PUT', 'GET'])
@cross_origin()
def profile_route(user_id):
    if request.method == 'PUT':
        if not request.is_json:
            return jsonify({"message": "Invalid request format, JSON required."}), 400

        data = request.get_json()
        bio = data.get('bio', None)  # Default to None if 'bio' not provided
        profile_image = data.get('profile_image', None)  # Same for 'profile_image'

        try:
            user = User.query.get(user_id)
            if not user:
                return jsonify({"message": "User not found"}), 404

            if not user.profile:
                user.profile = Profile(user_id=user_id)

            if bio is not None:
                user.profile.bio = bio
            if profile_image is not None:
                user.profile.profile_image = profile_image

            db.session.commit()
            return jsonify({"message": "Profile updated successfully"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"message": "Internal server error"}), 500

    elif request.method == 'GET':
        try:
            user = User.query.get(user_id)
            if not user:
                return jsonify({"message": "User not found"}), 404

            if not user.profile:
                return jsonify({"message": "Profile not found for this user"}), 404

            profile_data = {
                'username': user.username,
                'bio': user.profile.bio,
                'profile_image': user.profile.profile_image
            }
            return jsonify(profile_data), 200
        except Exception as e:
            return jsonify({"message": "Internal server error"}), 500

    else:
        return jsonify({"message": "Method not allowed"}), 405

        
@app.route('/search', methods=['GET'])
@cross_origin()
def search_users():
    query = request.args.get('q')
    if not query:
        return jsonify({"message": "Missing search query"}), 400
    users = User.query.filter(User.username.like(f"%{query}%")).all()
    return jsonify([{"user_id": user.id, "username": user.username} for user in users]), 200

@app.route('/follow/<int:followed_id>', methods=['POST'])
@cross_origin()
def follow_user(followed_id):
    current_user_id = request.json.get('current_user_id')
    current_user = User.query.get(current_user_id)
    if not current_user:
        return jsonify({"message": "Current user not found."}), 404

    user_to_follow = User.query.get(followed_id)
    if not user_to_follow:
        return jsonify({"message": "User to follow not found."}), 404
    
    if current_user.is_following(user_to_follow):
        return jsonify({"message": "Already following."}), 400
    
    current_user.follow(user_to_follow)
    db.session.commit()
    return jsonify({"message": "Now following."}), 200

@app.route('/unfollow/<int:followed_id>', methods=['POST'])
def unfollow_user(followed_id):
    current_user_id = request.json.get('current_user_id')
    current_user = User.query.get(current_user_id)
    if not current_user:
        return jsonify({"message": "Current user not found."}), 404

    user_to_unfollow = User.query.get(followed_id)
    if not user_to_unfollow:
        return jsonify({"message": "User to unfollow not found."}), 404
    
    if not current_user.is_following(user_to_unfollow):
        return jsonify({"message": "Not following this user."}), 400
    
    current_user.unfollow(user_to_unfollow)
    db.session.commit()
    return jsonify({"message": "Unfollowed."}), 200


if __name__ == '__main__':
     app.run()