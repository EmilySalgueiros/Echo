from flask import Flask, request, jsonify, session, redirect
from flask_cors import CORS, cross_origin
from backend.models import db, User, Profile, Post
from backend.services import login, register
import os
import requests
from flask_migrate import Migrate
<<<<<<< Updated upstream
=======
import requests
>>>>>>> Stashed changes
from urllib.parse import urlencode

# Create the Flask application
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

# Configure database
database_url = os.environ.get('CLEARDB_DATABASE_URL').replace(
    'mysql://', 'mysql+pymysql://')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SESSION_COOKIE_NAME'] = 'session'
app.config['SESSION_COOKIE_SECURE'] = True  # True for prod, False for dev
app.config['REMEMBER_COOKIE_SECURE'] = True  # True for prod, False for dev
# Prevents JavaScript access to session cookie
app.config['SESSION_COOKIE_HTTPONLY'] = True
# 'None' if cookies should be sent in all cross-origin requests
app.config['SESSION_COOKIE_SAMESITE'] = 'None'


# Configure SQLAlchemy engine options
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 299,
    'pool_pre_ping': True
}

db.init_app(app)
migrate = Migrate(app, db)

# Configure CORS
CORS(app, support_credentials=True, origins=["http://localhost:3000"])

# App Routes


@app.route('/')
def home():
    return 'Welcome to the Echo App!'


@app.route('/login', methods=['POST'])
@cross_origin(supports_credentials=True, origins=["http://localhost:3000"])
def login_route():
    if request.method == 'POST':
        username = request.json['username']
        password = request.json['password']
        user, status_code = login(username, password)
        if user:
            session['user_id'] = user['user_id']
            # Construct Spotify Authorization URL
            query_params = {
                'client_id': os.environ['SPOTIFY_CLIENT_ID'],
                'response_type': 'code',
                'redirect_uri': os.environ['SPOTIFY_REDIRECT_URI'],
                'scope': os.environ['SPOTIFY_REQUIRED_SCOPES'],
                'show_dialog': 'true'
            }
            spotify_auth_url = f"https://accounts.spotify.com/authorize?{
                urlencode(query_params)}"
            return redirect(spotify_auth_url)
        else:
            return jsonify({"message": "Invalid username or password"}), status_code


@app.route('/spotify_callback')
def spotify_callback():
    error = request.args.get('error')
    code = request.args.get('code')
    if error:
        return jsonify({'message': 'Authorization with Spotify failed.'}), 400

    # Exchange code for access token
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': os.environ['SPOTIFY_REDIRECT_URI'],
        'client_id': os.environ['SPOTIFY_CLIENT_ID'],
        'client_secret': os.environ['SPOTIFY_CLIENT_SECRET'],
    }
    response = requests.post(
        'https://accounts.spotify.com/api/token', data=token_data)
    response_data = response.json()

    if response.status_code != 200:
        return jsonify({'message': 'Failed to retrieve access token from Spotify.'}), response.status_code
<<<<<<< Updated upstream

    # Save tokens in the database
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    user.spotify_access_token = response_data['access_token']
    user.spotify_refresh_token = response_data['refresh_token']
    db.session.commit()

    # Redirect to a safe, logged-in page
    return redirect('http://localhost:3000/')
=======
>>>>>>> Stashed changes


@app.route('/register', methods=['POST', 'GET'])
@cross_origin(supports_credentials=True, origins=["http://localhost:3000"])
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
@cross_origin(supports_credentials=True, origins=["http://localhost:3000"])
def profile_route(user_id):
    if request.method == 'PUT':
        if not request.is_json:
            return jsonify({"message": "Invalid request format, JSON required."}), 400

        data = request.get_json()
        bio = data.get('bio', None)  # Default to None if 'bio' not provided
        # Same for 'profile_image'
        profile_image = data.get('profile_image', None)

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
                # Log for debugging
                print(f"User with ID {user_id} not found.")
                return jsonify({"message": "User not found"}), 404

            profile_data = {
                'username': user.username,
                'bio': user.profile.bio if user.profile else ""
            }
            return jsonify(profile_data), 200
        except Exception as e:
            print(f"Error fetching profile for user {
                  user_id}: {e}")  # Log detailed error
            return jsonify({"message": "Internal server error"}), 500

    else:
        return jsonify({"message": "Method not allowed"}), 405


@app.route('/posts', methods=['GET'])
@cross_origin(supports_credentials=True, origins=["http://localhost:3000"])
def get_posts():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"message": "Authentication required."}), 401

    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"message": "User not found"}), 404

        posts = [
            {
                "id": post.id,
                "song_recommendation": post.song_recommendation,
                "description": post.description,
                "created_at": post.created_at.isoformat()
            } for post in user.posts
        ]
        return jsonify(posts), 200
    except Exception as e:
        return jsonify({"message": "Internal server error", "error": str(e)}), 500


@app.route('/post', methods=['POST'])
@cross_origin(supports_credentials=True, origins=["http://localhost:3000"])
def create_post():
    print("Session user_id at /post:", session.get('user_id'))  # Debug print
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"message": "Authentication required."}), 401
    data = request.json
    new_post = Post(
        user_id=session['user_id'],
        song_recommendation=data['song_recommendation'],
        description=data.get('description', '')
    )
    db.session.add(new_post)
    try:
        db.session.commit()
        return jsonify({"message": "Post created successfully", "post_id": new_post.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create post", "error": str(e)}), 500


@app.route('/post/<int:post_id>', methods=['DELETE'])
@cross_origin(supports_credentials=True, origins=["http://localhost:3000"])
def delete_post(post_id):
    post = Post.query.get(post_id)
    if not post:
        return jsonify({"message": "Post not found"}), 404
    if post.user_id != session.get('user_id'):
        return jsonify({"message": "Unauthorized"}), 403
    db.session.delete(post)
    db.session.commit()
    return jsonify({"message": "Post deleted successfully"}), 200


if __name__ == '__main__':
    app.run()
