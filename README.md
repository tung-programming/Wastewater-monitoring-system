# 💧 Real-Time Wastewater Monitoring System using Machine Learning

This project is an IoT-based real-time wastewater quality monitoring system powered by machine learning. It uses sensor inputs (pH, temperature, turbidity, TDS) to predict critical environmental parameters like BOD, COD, and DO through trained Random Forest models. The system provides real-time analysis and classification via a Flask-based web dashboard.

---

## Features

- Real-time sensor data acquisition via Arduino
- Prediction of BOD, COD, DO using Random Forest Regression
- Water quality classification (Good, Moderate, Hazardous)
- Auto-retraining with live data
- Simulation mode fallback if Arduino fails
- Web dashboard for visualization (using Flask + Socket.IO)

---

## Machine Learning Model

- **Input Features**: pH, Temperature, TDS, Turbidity
- **Predicted Outputs**: BOD, COD, DO
- **Algorithm Used**: Random Forest Regression
- **Training Data**: Integrated datasets sourced from [Kaggle](https://www.kaggle.com/) and cleaned using `pandas`
- **Performance Metrics**: RMSE and R² Score

---

## Tech Stack

- Python (Flask, pandas, scikit-learn, joblib, threading)
- Arduino (Sensor Interfacing via Serial)
- HTML + CSS + JavaScript (Frontend dashboard)
- Socket.IO (Real-time communication)

---

## Sensors Used

- **pH Sensor** (analog)
- **TDS Sensor** (analog)
- **Turbidity Sensor** (analog)
- **Temperature Sensor** (LM35 or equivalent)

---

## Getting Started

### Prerequisites

- Python 3.7+
- Arduino IDE
- Sensors connected to analog pins of Arduino (A0–A4)
- COM port info (e.g., `COM7`, `/dev/ttyUSB0`)

### Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/yourusername/wastewater-monitoring-ml.git
   cd wastewater-monitoring-ml


   ```

2. Install Python dependencies:

   ```bash
   pip install -r requirements.txt

   ```

3. Upload the Arduino code (arduino_code.ino) to your Arduino board.

4. Start the backend server:

   ```bash
   python app.py

   ```

5. Open your browser and navigate to:
   http://127.0.0.1:5000

## Dashboard Preview

The live dashboard displays:

-Current sensor values

-Predicted BOD, COD, DO

-Water quality status and explanation

-Feature importance (per model)

## Folder Structure

```bash
├── python_backend/
│   ├── app.py                # Main backend script
│   ├── wastewater_data.csv   # Training + live data
│   ├── models/               # Saved ML models (.pkl)
│
├── templates/
│   └── index.html            # Flask frontend
├── static/
│   ├── style.css
│   └── dashboard.js
├── arduino_code/
│   └── arduino_code.ino
├── README.md
├── LICENSE.md
```

## Notes

-If the Arduino is not connected or busy, the system will switch to simulation mode and display dummy values.

-Models are retrained in the background using new sensor readings.

-The logic used for sensor readings in arduino will differ, so make sure to Calibrate the sensors

## Author
Tushar P | Email: tusharpradeep24@gmail.com | Github:@tung-programming

## License

[MIT LICENSE](LICENSE.md)
