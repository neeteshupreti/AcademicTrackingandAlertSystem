# ATAS: Academic Tracking and Alert System 🎓

**ATAS** is a Django-based web application designed to automate the detection and tracking of students requiring compartment (re-take) exams. By leveraging **Optical Character Recognition (OCR)** and **Pandas Data Processing**, ATAS eliminates manual grade entry and identifies at-risk students instantly.

## 🚀 Key Features

- **🔍 Universal Smart Scanner (OCR):** Uses Tesseract and OpenCV to extract data from any transcript format (e.g., Kathmandu University, Aspire College)
- **⚠️ Automated Failure Detection:** Instantly flags students with a GPA < 2.0 or specific failing grades (F, D, or incomplete 'X')
- **📤 Bulk CSV/Excel Upload:** Integrated Pandas engine for processing entire semester result sheets
- **🗂️ Relational Academic Tracking:** Manages Faculty, Courses, Students, and Exam Deadlines with database relationships
- **📱 Live Camera Integration:** Scan physical documents directly from the browser using webcam

## 🛠️ Tech Stack

| Layer | Technology |
| --- | --- |
| **Backend** | Python 3.10+, Django 4.x |
| **Data Processing** | Pandas, NumPy |
| **Computer Vision** | Pytesseract, Tesseract OCR, OpenCV, Pillow |
| **Frontend** | HTML5, Bootstrap 5, CSS3, JavaScript (Webcam API) |
| **Database** | SQLite (Development), PostgreSQL (Production-ready) |

## ⚙️ Installation & Setup

### Prerequisites
Ensure you have the following installed:

#### System Requirements
- **Python 3.10+**
- **Tesseract OCR**
  - **Linux:** `sudo apt install tesseract-ocr`
  - **macOS:** `brew install tesseract`
  - **Windows:** Download from [Tesseract OCR Releases](https://github.com/UB-Mannheim/tesseract/wiki)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/neeteshupreti/AcademicTrackingandAlertSystem.git
   cd AcademicTrackingandAlertSystem
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser account**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Admin Panel: http://localhost:8000/admin
   - Main App: http://localhost:8000

## 📁 Project Structure

```
AcademicTrackingandAlertSystem/
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
├── db.sqlite3               # SQLite database
├── ATAS/                    # Django configuration
│   ├── settings.py          # Project settings
│   ├── urls.py              # Main URL routing
│   └── wsgi.py
├── core/                    # Core application
│   ├── views.py            # Admin & main views
│   ├── models.py           # Core models
│   ├── urls.py
│   └── templates/          # HTML templates
├── students/               # Students management app
│   ├── views.py           # Student views & import logic
│   ├── models.py          # Student models
│   ├── forms.py           # Django forms
│   └── templates/         # Student templates
├── notifications/         # Notifications app
│   ├── views.py
│   ├── models.py          # Alert models
│   └── templates/
└── static/               # Static assets
    ├── css/             # Stylesheets
    └── js/              # JavaScript files
```

## 🎯 Usage

### Admin Dashboard
1. Log in with superuser credentials
2. Manage Faculty, Courses, and Students
3. Set compartment deadlines
4. Monitor active alerts

### Upload Student Records
1. Navigate to **Import Records** section
2. Choose between:
   - **File Upload:** Upload CSV/Excel with student results
   - **Camera Scanner:** Capture transcript photos with webcam
3. System automatically detects failures and creates alerts

### View Alerts
- Dashboard displays all active compartment alerts
- Sorted by deadline urgency
- Track student status in real-time

## 🔧 Configuration

Edit `ATAS/settings.py` to customize:
- Database settings
- Tesseract path (if not in system PATH)
- Email notifications (SMTP configuration)
- Static/Media file locations

## 📝 Notes

- **Tesseract Path:** If Tesseract isn't in your system PATH, add to `settings.py`:
  ```python
  import pytesseract
  pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows
  ```

- **Database:** SQLite is included for development. For production, configure PostgreSQL in `settings.py`

## 🤝 Contributing

Pull requests are welcome! Please follow Django coding standards and include tests for new features.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 📧 Contact & Support

For issues, questions, or contributions, please open an issue on GitHub or reach out to the development team.
