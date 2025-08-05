from flask import (
    Flask,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    Response,
    session,
    url_for,
)

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from flask_sqlalchemy import SQLAlchemy
from jinja2.exceptions import TemplateNotFound
from werkzeug.security import check_password_hash, generate_password_hash

# Initialise Flask instance
app = Flask(__name__)

# Alter Flask timeout
app.config['TIMEOUT'] = 600

# Configure database URI and create database instance
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# Session key
app.secret_key = '7EDYZ8pak3Px'

# Homepage route
@app.route('/')
def homepage():
    return render_template("/homepage.html")

# Machine learning route
@app.route('/ml/<int:roundnum>')
def get_ml_predictions(roundnum):
    round_num = int(roundnum)
    print('ML running',round_num)

    data = pd.read_csv('f1_dataset.csv')

    df = data.copy()

    train = df[df.season <2023]
    X_train = train.drop(['driver', 'podium'], axis=1)
    y_train = train.podium

    scaler = StandardScaler()
    X_train = pd.DataFrame(scaler.fit_transform(X_train), columns=X_train.columns)

    def regression_predictions(model):
        all_predictions = pd.DataFrame({'round': [], 'predicted': [], 'actual': [], 'driver': [], 'probability': []})

        for circuit in pd.DataFrame(df[df.season == 2023])['round'].unique():
            test = df[(df.season == 2023) & (df['round'] == circuit)]
            X_test = test.drop(['driver', 'podium'], axis=1)

            X_test = pd.DataFrame(scaler.transform(X_test), columns=X_test.columns)

            # Make predictions
            probabilities = model.predict_proba(X_test)[:, 1]

            # Assign predicted positions based on probabilities
            prediction_df = pd.DataFrame({'probability': probabilities, 'driver': test['driver']})
            prediction_df['predicted'] = prediction_df['probability'].rank(ascending=False, method='first')

            # Tie handling
            prediction_df['predicted'] += np.random.uniform(0, 1e-6, size=len(prediction_df))

            # Sort predictions by position
            prediction_df.sort_values('predicted', inplace=True)

            # Ensure predicted positions for drivers are full
            prediction_df['predicted'] = prediction_df.groupby('predicted').ngroup() + 1
            if len(prediction_df) < 20:
                missing_positions = set(range(1, 21)) - set(prediction_df['predicted'])
                missing_drivers = prediction_df['driver'].tail(20 - len(prediction_df))
                missing_predictions = pd.DataFrame({'predicted': list(missing_positions), 'driver': missing_drivers})
                prediction_df = pd.concat([prediction_df, missing_predictions])

            prediction_df['actual'] = test['podium']
            prediction_df['round'] = circuit

            # Store predicted and actual podium along with driver names
            all_predictions = pd.concat([all_predictions, prediction_df[['round', 'predicted', 'actual', 'driver', 'probability']]], ignore_index=True)  # Include 'probability' column here
        return all_predictions

    # Train model
    model = LogisticRegression(solver='lbfgs')
    model.fit(X_train, y_train)

    # Call the regression_predictions function with the trained model
    all_predictions = regression_predictions(model)


    def top_5_round_prediction(prediction_df, round_num):
        top_5_winners_data = []

        round_predictions = prediction_df[prediction_df['round'] == round_num]
        sorted_predictions = round_predictions.sort_values(by='predicted')

        # Get top 5 predicted winners and their likelihood
        top_5_drivers = sorted_predictions['driver'].head(5).tolist()
        top_5_probs = (sorted_predictions['probability'] * 100).round(2).head(5).tolist()  # Convert to percentage format with 2 decimal places

        # Error handling
        if len(top_5_drivers) < 5:
            top_5_drivers.extend([None] * (5 - len(top_5_drivers)))
            top_5_probs.extend([0.00] * (5 - len(top_5_probs)))

        top_5_winners_data.append({
            'round': round_num,
            '1st_predicted': top_5_drivers[0],
            '1st_predicted_chance': f"{top_5_probs[0]:.2f}%",
            '2nd_predicted': top_5_drivers[1],
            '2nd_predicted_chance': f"{top_5_probs[1]:.2f}%",
            '3rd_predicted': top_5_drivers[2],
            '3rd_predicted_chance': f"{top_5_probs[2]:.2f}%",
            '4th_predicted': top_5_drivers[3],
            '4th_predicted_chance': f"{top_5_probs[3]:.2f}%",
            '5th_predicted': top_5_drivers[4],
            '5th_predicted_chance': f"{top_5_probs[4]:.2f}%",
        })

        # Convert list of dictionaries to DataFrame
        top_5_winners_df = pd.DataFrame(top_5_winners_data)

        return top_5_winners_df

    top_5_winners_df = top_5_round_prediction(all_predictions, round_num)

    # Convert to JSON
    def get_top_5_winners_json(top_5_winners_df):
        if top_5_winners_df is not None:
            return top_5_winners_df.to_json(orient='records'), 200, {'Content-Type': 'application/json'}
        else:
            return '[]', 200, {'Content-Type': 'application/json'}  # Return empty JSON array
    json_data, status_code, headers = get_top_5_winners_json(top_5_winners_df)
    return Response(response=json_data, status=status_code, headers=headers)

# Render individual track pages if they exist
@app.route('/tracks/<trackname>')
def tracks(trackname):
    try:
        return render_template("/tracks/"+trackname+".html")
    except TemplateNotFound:
        return render_template("/homepage.html")

# Run Flask application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)