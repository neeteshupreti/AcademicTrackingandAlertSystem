# ATAS: Academic Tracking and Alert System 🎓

**ATAS** is a Django-based management system designed to automate the detection and tracking of students requiring compartment (re-take) exams. By leveraging **Optical Character Recognition (OCR)** and **Pandas Data Processing**, ATAS eliminates manual grade entry and identifies at-risk students in seconds.



## 🚀 Key Features

- **Universal Smart Scanner (OCR):** Uses Tesseract and OpenCV to extract data from any transcript format (e.g., Kathmandu University, Aspire College).
- **Automated Failure Detection:** Instantly flags students with a GPA < 2.0 or specific failing grades (F, D, or incomplete 'X').
- **Bulk CSV/Excel Upload:** Integrated Pandas engine for processing entire semester result sheets.
- **Relational Academic Tracking:** Manages links between Faculty, Courses, Students, and Exam Deadlines.
- **Live Camera Integration:** Accesses webcam directly from the browser to scan physical documents.

## 🛠️ Tech Stack

- **Backend:** Python / Django
- **Data Processing:** Pandas
- **Computer Vision:** Pytesseract (Tesseract OCR), OpenCV, Pillow
- **Frontend:** HTML5, Bootstrap 5, JavaScript (Webcam API)
- **Database:** SQLite (Development)

## 📸 System Preview

| Feature | Description |
| :--- | :--- |
| **Dashboard** | Overview of active alerts and total student statistics. |
| **Import Center** | Toggle between File Upload and Live Camera Scanner. |
| **Smart Parser** | Converts messy OCR text into structured academic records. |



## ⚙️ Installation

### 1. Prerequisites
Ensure you have **Tesseract OCR** installed on your system:
- **Linux:** `sudo apt install tesseract-ocr`
- **Windows:** Download the binary from [Tesseract OCR github](https://github.com/UB-Mannheim/tesseract/wiki).

### 2. Setup Environment
```bash
# Clone the repository
git clone [https://github.com/yourusername/ATAS-System.git](https://github.com/yourusername/ATAS-System.git)
cd ATAS-System

# Install dependencies
pip install django pandas pytesseract opencv-python pillow
