"""
Main Python backend script for the Real-Time Wastewater Monitoring System.
(Version with improved error reporting for training failures)
"""

import os
import serial
import time
import random
import threading
import pandas as pd
from flask import Flask, render_template
from flask_socketio import SocketIO
from sklearn.ensemble import RandomForestRegressor
import joblib

# --- 1. CONFIGURATION ---
USE_ARDUINO = True
SERIAL_PORT = 'COM7' 
BAUD_RATE = 9600

# --- 2. GLOBAL VARIABLES & SETUP ---
app = Flask(__name__, template_folder='../templates', static_folder='../static')
socketio = SocketIO(app)
data_file = 'wastewater_data.csv'
models_dir = 'models'
model_paths = {
    'BOD': os.path.join(models_dir, 'bod_model.pkl'),
    'COD': os.path.join(models_dir, 'cod_model.pkl'),
    'DO': os.path.join(models_dir, 'do_model.pkl')
}
thread = None

# --- 3. MACHINE LEARNING & DATA HANDLING FUNCTIONS ---

def train_models(retrain=False):
    """Cleans data, then trains models for BOD, COD, and DO."""
    if not retrain and all(os.path.exists(p) for p in model_paths.values()):
        print("Models already exist. Skipping initial training.")
        return False # Return False to indicate no training was done

    print("--- Starting Model Training ---")
    socketio.emit('training_status', {'status': 'Loading and cleaning data...'})
    
    try:
        df = pd.read_csv(data_file)
        print(f"Initial dataset loaded with {len(df)} rows.")
        print(f"Found columns: {list(df.columns)}") # <-- IMPROVED DEBUGGING

        # Check for missing columns FIRST
        features = ['pH', 'TDS', 'Turbidity', 'Temperature']
        targets = ['BOD', 'COD', 'DO']
        required_cols = features + targets
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            # <-- IMPROVED DEBUGGING MESSAGE
            print("\n" + "="*60)
            print("FATAL ERROR: Your CSV file is missing required columns!")
            print(f"Missing Column(s): {', '.join(missing_cols)}")
            print(f"Please ensure your CSV header contains these exact (case-sensitive) names: {', '.join(required_cols)}")
            print("="*60 + "\n")
            socketio.emit('training_status', {'status': f"Error: CSV missing columns: {', '.join(missing_cols)}"})
            return False # Stop training

        # Data cleaning
        df.dropna(subset=required_cols, inplace=True)
        print(f"Data cleaned. {len(df)} complete rows remain for training.")
            
        socketio.emit('training_status', {'status': 'Data cleaned. Starting model training...'})

        X = df[features]
        if not os.path.exists(models_dir): os.makedirs(models_dir)

        for target in targets:
            print(f"  Training model for {target}...")
            y = df[target]
            model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1) 
            model.fit(X, y)
            joblib.dump(model, model_paths[target])
        
        print("--- Model Training Successful ---")
        socketio.emit('training_status', {'status': 'Models trained! System is now live.'})
        return True # Return True on success

    except FileNotFoundError:
        print(f"ERROR: The data file '{data_file}' was not found in the 'python_backend' folder.")
        socketio.emit('training_status', {'status': f"Error: {data_file} not found."})
        return False
    except Exception as e:
        print(f"An unexpected error occurred during training: {e}")
        socketio.emit('training_status', {'status': f"Training Error: {e}"})
        return False

def update_and_retrain(new_data_row):
    """Appends a new row to the CSV and retrains the models."""
    try:
        original_cols = pd.read_csv(data_file, nrows=0).columns
        df_new = pd.DataFrame([new_data_row])
        df_new = df_new.reindex(columns=original_cols, fill_value=pd.NA)
        df_new.to_csv(data_file, mode='a', header=False, index=False)
        train_models(retrain=True)
    except Exception as e:
        print(f"Error during self-learning (update_and_retrain): {e}")

# --- (The rest of the file is the same as the previous version) ---

# --- 4. WATER QUALITY ANALYSIS ---
def classify_water(inputs, predictions):
    ph, turbidity, do, bod = inputs['pH'], inputs['Turbidity'], predictions['DO'], predictions['BOD']
    reasons, moderate_reasons = [], []
    if not (6.5 <= ph <= 8.5): reasons.append(f"pH ({ph:.1f}) is outside safe range (6.5-8.5)")
    if turbidity > 5: reasons.append(f"Turbidity ({turbidity:.1f} NTU) is too high (> 5)")
    if do < 4: reasons.append(f"DO ({do:.1f} mg/L) is too low (< 4)")
    if bod > 6: reasons.append(f"BOD ({bod:.1f} mg/L) is too high (> 6)")
    if reasons: return {"status": "Hazardous", "reasons": reasons}
    if turbidity > 1: moderate_reasons.append(f"Turbidity ({turbidity:.1f} NTU) is elevated (> 1)")
    if do < 5: moderate_reasons.append(f"DO ({do:.1f} mg/L) is low (< 5)")
    if bod > 2: moderate_reasons.append(f"BOD ({bod:.1f} mg/L) is elevated (> 2)")
    if moderate_reasons: return {"status": "Moderate", "reasons": moderate_reasons}
    return {"status": "Good", "reasons": ["All parameters are within optimal range."]}

# --- 5. BACKGROUND DATA READING THREAD ---
def background_thread():
    global USE_ARDUINO
    print("--- Starting Background Data Thread ---")
    serial_connection = True
    if USE_ARDUINO:
        try:
            serial_connection = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
            print(f"Successfully connected to Arduino on {SERIAL_PORT}")
        except serial.SerialException as e:
            print(f"Warning: Arduino connection failed: {e}. Falling back to simulation mode.")
            USE_ARDUINO = False 
    try:
        models = {target: joblib.load(path) for target, path in model_paths.items()}
        print("ML models loaded successfully for prediction.")
    except Exception as e:
        print(f"FATAL ERROR: Could not load ML models. {e}")
        socketio.emit('training_status', {'status': 'Error: Could not load ML models. Please restart.'})
        return
    while True:
        try:
            inputs = {}
            if USE_ARDUINO and serial_connection:
                line = serial_connection.readline().decode('utf-8').strip()
                print(f"Received data from Arduino: {line}")
                if line and len(line.split(',')) == 4:
                    parts = line.split(',')
                    inputs = { 'pH': float(parts[0]), 'TDS': float(parts[1]), 'Turbidity': float(parts[2]), 'Temperature': float(parts[3]) }
                else: continue
            else:
                inputs = { 'pH': round(random.uniform(6.0, 9.0), 2), 'TDS': round(random.uniform(300, 1000), 2), 'Turbidity': round(random.uniform(0.5, 8.0), 2), 'Temperature': round(random.uniform(20, 35), 2) }
                #inputs = { 'pH': 7, 'TDS': 50, 'Turbidity':1, 'Temperature': 20 }
            input_df = pd.DataFrame([inputs])
            predictions = { 'BOD': round(models['BOD'].predict(input_df)[0], 2), 'COD': round(models['COD'].predict(input_df)[0], 2), 'DO': round(models['DO'].predict(input_df)[0], 2) }
            importances = { 'BOD': {k: round(v*100, 1) for k, v in zip(input_df.columns, models['BOD'].feature_importances_)}, 'COD': {k: round(v*100, 1) for k, v in zip(input_df.columns, models['COD'].feature_importances_)}, 'DO': {k: round(v*100, 1) for k, v in zip(input_df.columns, models['DO'].feature_importances_)} }
            quality = classify_water(inputs, predictions)
            data_packet = { 'inputs': inputs, 'predictions': predictions, 'quality': quality, 'importances': importances }
            socketio.emit('update_data', data_packet)
            new_row_for_csv = {**inputs, **predictions}
            retrain_thread = threading.Thread(target=update_and_retrain, args=(new_row_for_csv,))
            retrain_thread.start()
        except Exception as e:
            print(f"An error occurred in the background thread: {e}")
            time.sleep(2)
        socketio.sleep(5)

# --- 6. FLASK & SOCKETIO ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')
@socketio.on('connect')
def handle_connect(*args, **kwargs):
    global thread
    print('Client connected')
    if thread is None:
        print("Starting new background thread.")
        thread = socketio.start_background_task(target=background_thread)

# --- 7. SCRIPT EXECUTION ---
if __name__ == '__main__':
    models_trained = train_models()
    if models_trained:
        print("="*50)
        print("Server is starting...")
        print(f"Open http://127.0.0.1:5000 in your web browser.")
        print("="*50)
        socketio.run(app, debug=True, use_reloader=False)
    else:
        print("="*50)
        print("Server did not start due to a training error.")
        print("Please check the error messages above and fix your CSV file.")
        print("="*50)