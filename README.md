# 🏥 Doctor POS Clinic System

A simple **desktop-based Point of Sale (POS) system** built in **Python** with **Tkinter** and **SQLite**, designed for small clinics.  
This system allows doctors to manage patients, medicines, stock, billing, and generate printable invoices — all in one place.  

---

## 📌 Features

- 👨‍⚕️ **Doctor Login** (only doctor use, no receptionist access)  
- 💊 **Medicine Management** (add, update, delete medicines)  
- 📦 **Stock Tracking** (automatically reduces stock after each sale)  
- 🧾 **Billing System**  
  - Add medicines prescribed to patient  
  - Include doctor’s consultation fee  
  - Calculate **total bill (doctor fee + medicines)**  
- 🖨 **Invoice Printing (PDF)** using ReportLab  
- 📊 **Simple, easy-to-use interface** (desktop application, no internet required)  
- 💾 **Data stored locally** using SQLite database  

---

## 🛠️ Tech Stack

- **Python 3.x**  
- **Tkinter** → GUI (desktop app)  
- **SQLite3** → Local database  
- **ReportLab** → Invoice PDF generation  

---

## 📂 Project Structure

Doctor POS Clinic/
│
├── services/ # Business logic (billing, inventory updates, etc.)
├── ui/ # User interface (Tkinter forms, windows)
├── app.py # Main entry point of the system
├── db.py # Database setup and models
├── requirements.txt # Python dependencies
├── .gitignore # Ignored files (cache, dist, etc.)
└── README.md # Project documentation


</details>

---

## 🚀 Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/your-username/doctor-pos-clinic.git
cd doctor-pos-clinic
### 2. Create virtual environment (optional but recommended)

```bash
python -m venv venv

### 3. Install dependencies
```bash
pip install -r requirements.txt

### 4. Run the app
```bash
python app.py

## 📸 Screenshots  

👉 (Add your screenshots here once the app is running. Example placeholders below:)  

- Add Medicine
<img width="1366" height="929" alt="image" src="https://github.com/user-attachments/assets/bd06175c-3be0-411c-82b5-6da100fcf3fc" />
-Add Patients
<img width="1375" height="944" alt="image" src="https://github.com/user-attachments/assets/8797621b-406f-442a-9936-6120b9dce325" />

- Billing Screen
<img width="1377" height="931" alt="image" src="https://github.com/user-attachments/assets/8de3bdfa-7461-4e57-a44d-85e7b4c52843" />

- Generated Invoice (PDF)  
<img width="1915" height="767" alt="image" src="https://github.com/user-attachments/assets/dba3947a-d4dc-49ab-989d-4dccb3bb80ef" />

## 📖 Usage  

1. Start the app (`python app.py`).    
2. Add medicines with prices and stock.  
3. When a patient comes:  
   - Enter medicines given  
   - Enter doctor’s consultation fee  
   - System calculates total bill  
   - Generate and print invoice  
## ⚡ Roadmap / Future Improvements  

- Multi-user support (receptionist + doctor roles)  
- Patient history tracking  
- Search & filter medicines  
- Export sales report to Excel  
## 🤝 Contribution  

Contributions are welcome!  
If you’d like to improve this project:  

1. Fork this repo  
2. Create a new branch (`feature-xyz`)  
3. Commit changes and push  
4. Open a Pull Request  
