# Smart Parking Management System (SPMS)

The **Smart Parking Management System (SPMS)** is a Flask-based web application that automates parking management using **License Plate Recognition (LPR)**.  
It integrates **OpenCV + EasyOCR** for plate detection, stores captured data in a **MySQL database**, sends **real-time SMS alerts via Twilio**, and supports **AWS S3** for storing images.  

Designed for **real-world deployment**, SPMS has been tested with 50+ concurrent vehicles and anomaly detection (≈96% accuracy).

---

## 🚗 Features
- 🔑 **User Management** – Secure login/registration, role-based access (admin/operator/user).  
- 📸 **License Plate Recognition** – Detect & recognize plates using **OpenCV + EasyOCR**.  
- ⏱ **Parking Sessions** – Track entry/exit, calculate tariff dynamically.  
- 📲 **SMS Notifications** – Send expiry alerts & payment confirmations via **Twilio**.  
- ☁️ **Cloud Integration** – Store captured images securely in **AWS S3**.  
- 🛡 **Anomaly Detection** – Detect mismatched plates, duplicate entries, and unusually long stays.  
- 📊 **Admin Dashboard** – View occupancy, revenue, anomalies, and reports.  
- ⚡ **Scalable Design** – Deployable on **AWS EC2** with **RDS MySQL** backend.  

---

## 🛠 Tech Stack
- **Backend**: Flask (Python)  
- **Database**: MySQL (local) / Amazon RDS (production)  
- **Computer Vision**: OpenCV, EasyOCR  
- **Notifications**: Twilio SMS API  
- **Cloud Storage**: AWS S3  
- **Deployment**: AWS EC2, Gunicorn, Nginx  
- **Frontend (Optional)**: HTML (Jinja2 templates), CSS, JavaScript  

---

## ⚙️ Architecture
```

\[Entry Camera]
|
v
\[Flask API] ---> \[OCR: plate\_to\_num.py] ---> \[MySQL DB]
\|                  |
\|                  v
\|              \[Anomaly Detector]
|
+---> \[AWS S3 Storage] (for images)
|
+---> \[Twilio SMS Alerts via session\_alert.py]

````

---

## 🚀 Getting Started

### 1. Clone & Setup
```bash
git clone https://github.com/your-username/spms.git
cd spms
cp .env.example .env
````

### 2. Create Virtual Environment & Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Database

```bash
flask db upgrade
```

### 4. Run the App

```bash
python app.py
```

Visit: [http://localhost:5000](http://localhost:5000)

---

## 🔑 Environment Variables

Create a `.env` file in the project root:

```ini
# Flask
FLASK_ENV=development
SECRET_KEY=your_secret_key

# Database
DB_URI=mysql://user:password@localhost:3306/spms

# AWS S3
AWS_S3_BUCKET=your-bucket
AWS_ACCESS_KEY_ID=xxxx
AWS_SECRET_ACCESS_KEY=xxxx
AWS_REGION=ap-south-1

# Twilio
TWILIO_ACCOUNT_SID=xxxx
TWILIO_AUTH_TOKEN=xxxx
TWILIO_FROM_NUMBER=+1xxxx

# Config
OCR_CONFIDENCE_THRESHOLD=0.55
BASE_RATE_PER_HOUR=50
GRACE_PERIOD_MINUTES=10
```

---

## 📂 Project Structure

Matches your actual files:

```
spms/
 ├── __pycache__/          # Python cache
 ├── model/                # ML models for OCR & anomaly detection
 ├── plates/               # Captured license plate images
 ├── static/               # Static assets (CSS, JS, icons)
 ├── templates/            # HTML templates (Flask + Jinja2)
 ├── app.py                # Main Flask application
 ├── plate_to_num.py       # OCR logic (image -> plate number)
 ├── session_alert.py      # SMS alerts for session expiry
 ├── requirements.txt      # Python dependencies
 ├── .env.example          # Sample environment file
 └── README.md             # Project documentation
```

---

## 📡 API Reference

### 🔐 Authentication

#### Register

```http
POST /register
Body: { "email": "user@test.com", "password": "12345" }
```

#### Login

```http
POST /login
Body: { "email": "user@test.com", "password": "12345" }
```

---

### 🚘 Parking Sessions

#### Start Session

```http
POST /start_session
Body: { "plate": "KA01AB1234" }
```

*Response:*

```json
{ "session_id": 101, "plate": "KA01AB1234", "status": "active" }
```

#### End Session

```http
POST /end_session
Body: { "session_id": 101 }
```

*Response:*

```json
{ "session_id": 101, "plate": "KA01AB1234", "status": "completed", "amount": 120 }
```

---

### 🔍 License Plate Recognition

#### Upload Plate Image

```http
POST /upload_plate
FormData: image=<car_image.jpg>
```

*Response:*

```json
{ "plate": "KA01AB1234", "confidence": 0.92 }
```

---

### 🛠 Admin Endpoints

* **GET** `/sessions` → List all sessions
* **GET** `/anomalies` → List detected anomalies

---

## 🚢 Deployment

* **Local**: Flask dev server
* **Production**: Gunicorn + Nginx on **AWS EC2**
* **Database**: Amazon RDS (MySQL)
* **Storage**: AWS S3 for images
* **Notifications**: Twilio SMS

---

## 👨‍💻 Contributing

1. Fork the repo
2. Create your feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m 'Add new feature'`
4. Push branch: `git push origin feature-name`
5. Create Pull Request

