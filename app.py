from flask import Flask, render_template, request, redirect, url_for, session
from utils.dish import DishManager
from utils.auth import get_dish_average_ratings, get_dish_counts, logout_user, get_logged_in_user, delete_history_function, login_required, rate_dish_function, store_google_user
from utils.db import create_tables, insert_dishes_from_csv
import os
from dotenv import load_dotenv
from flask_dance.contrib.google import make_google_blueprint, google

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '0' # production
# os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' # local environment
create_tables()
insert_dishes_from_csv()
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
manager = DishManager()
google_blueprint = make_google_blueprint(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    redirect_to='google_login'
)
app.register_blueprint(google_blueprint, url_prefix='/login')

@app.route('/')
def index():
    average_ratings = get_dish_average_ratings()  # Get average ratings
    dish_counts = get_dish_counts()  # Get counts
    username = get_logged_in_user()  # Get logged-in user
    return render_template('index.html', username=username, average_ratings=average_ratings, dish_counts=dish_counts)

@app.route('/google_login')
def google_login():
    # If the user is not authorized by Google
    if not google.authorized:
        return redirect(url_for('google.login'))
    
    # Get user info from Google
    resp = google.get('/oauth2/v1/userinfo')
    assert resp.ok, resp.text  # Ensure the request was successful
    user_info = resp.json()

    store_google_user(user_info)

    # Log the user in (using their Google username as a session identifier)
    session['username'] = user_info.get('name')  # Use Google name as username

    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/recommendation', methods=['POST'])
def recommendation():
    criteria = {key: value.lower() for key, value in request.form.items()}
    recommendation = manager.make_recommendation(**criteria)
    return render_template('recommendation.html', recommendation=recommendation)

@app.route('/food/<name>', methods=['GET', 'POST'])
@login_required
def food(name=None):
    dish = manager.get_food_by_name(name)
    manager.add_selection(get_logged_in_user(), name)
    return render_template('food.html', dish=dish)

@app.route('/history')
def history():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    user_history = manager.get_user_history(username)
    history_data = [{'id': record[0],'dish_name': record[1], 'timestamp': record[2], 'rating': record[3]} for record in user_history]
    return render_template('history.html', items=history_data)

@app.route('/delete_history', methods=['POST'])
def delete_history():
    history_id = request.form.get('history_id')
    if history_id:
        if delete_history_function(history_id):
            return redirect(url_for('history'))
    return redirect(url_for('history'))

@app.route('/rate_dish', methods=['POST'])
def rate_dish():
    history_id = request.form.get('history_id')
    rating = request.form.get('rating')

    if rate_dish_function(history_id, rating):
        return redirect(url_for('history'))
    return redirect(url_for('history'))

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)