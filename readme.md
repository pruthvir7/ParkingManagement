# Smart Parking Management System (SPMS)

A comprehensive parking management solution that automates vehicle entry/exit, tracks parking sessions, and provides real-time notifications using computer vision and cloud technologies.

## 🚀 Features

- **Automated License Plate Recognition (LPR)** - 96% accuracy using OpenCV and EasyOCR
- **User Registration & Authentication** - Secure user management system
- **Real-time Parking Session Tracking** - Monitor active parking sessions
- **SMS Notifications** - Automated alerts for session expiry via Twilio
- **Payment Integration** - Payment confirmation and processing
- **Anomaly Detection** - Advanced monitoring with 96% accuracy
- **Cloud Infrastructure** - Scalable deployment on AWS

## 🛠 Tech Stack

### Backend
- **Flask** - Python web framework
- **MySQL** - Database management
- **OpenCV** - Computer vision processing
- **EasyOCR** - Optical character recognition

### Cloud & Services
- **AWS EC2** - Application hosting
- **AWS S3** - Image storage
- **AWS RDS MySQL** - Managed database
- **Twilio** - SMS notification service

## 📁 Project Structure

```
spms/
├── __pycache__/          # Python bytecode cache
├── model/                # Machine learning models and OCR processing
├── plates/               # License plate images storage
├── static/               # Static web assets (CSS, JS, images)
├── templates/            # HTML templates for web interface
├── app.py               # Main Flask application (17 KB)
├── plate_to_num.py      # License plate number extraction logic (8 KB)
├── session_alert.py     # Session expiry and SMS alert system (6 KB)
└── requirements.txt     # Python dependencies
```

## 🔧 Core Application Files

### `app.py` (17 KB)
Main Flask application containing:
- Route definitions for web endpoints
- Database connection and models
- User authentication system
- Parking session management
- Integration with AWS services

### `plate_to_num.py` (8 KB)
License plate recognition module:
- OpenCV image preprocessing
- EasyOCR text extraction
- Plate number validation and formatting
- Integration with parking entry/exit system

### `session_alert.py` (6 KB)
Notification and alert system:
- Session expiry monitoring
- Twilio SMS integration
- Alert scheduling and management
- User notification preferences

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.8+
- MySQL 8.0+
- AWS Account
- Twilio Account

### Local Development

1. **Clone the repository**
```bash
git clone 
cd spms
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment Configuration**
Create a `.env` file in the root directory:
```env
FLASK_ENV=development
DATABASE_URL=mysql://username:password@localhost/spms_db
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1
S3_BUCKET_NAME=spms-images
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+1234567890
```

5. **Setup directories**
```bash
# Ensure plates directory exists for image storage
mkdir -p plates
```

6. **Database Setup**
```bash
mysql -u root -p
CREATE DATABASE spms_db;
# Import your database schema
```

7. **Run the application**
```bash
python app.py
```

## 🔧 Key Components

### License Plate Recognition (`plate_to_num.py`)
- Processes images from `plates/` folder
- Uses OpenCV for image preprocessing
- Implements EasyOCR for text extraction
- Returns formatted license plate numbers

### Session Management (`app.py`)
- Tracks vehicle entry/exit times
- Manages user parking sessions
- Integrates with payment systems
- Provides web dashboard through templates

### Alert System (`session_alert.py`)
- Monitors active parking sessions
- Sends SMS notifications via Twilio
- Handles session expiry warnings
- Manages notification scheduling

## 📊 File Organization

### `/model/`
Contains machine learning models and OCR processing files

### `/plates/`
Storage directory for captured license plate images

### `/static/`
Web assets including:
- CSS stylesheets
- JavaScript files
- Image resources
- UI components

### `/templates/`
HTML templates for:
- User dashboard
- Login/registration pages
- Parking status displays
- Admin panels

## 🚀 Deployment

### AWS EC2 Setup
```bash
# Transfer files to EC2
scp -r . ubuntu@your-ec2-instance:~/spms/

# Install dependencies on EC2
pip install -r requirements.txt

# Configure nginx/apache for production
# Set up SSL certificates
# Configure environment variables
```

### S3 Integration
- Upload plate images to S3 bucket
- Configure IAM roles for EC2 access
- Set up lifecycle policies for image cleanup

## 📱 Usage

1. **Start the application**
```bash
python app.py
```

2. **Access web interface**
- Navigate to `http://localhost:5000`
- Register/login to access dashboard

3. **License Plate Processing**
- Images captured automatically stored in `plates/`
- `plate_to_num.py` processes images for text extraction

4. **Session Monitoring**
- `session_alert.py` runs background monitoring
- SMS alerts sent for session expiry

## 🧪 Testing

Test the core components:
```bash
# Test license plate recognition
python plate_to_num.py

# Test session alerts
python session_alert.py

# Test main application
python app.py
```
