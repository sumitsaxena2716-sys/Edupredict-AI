# 🎓 Edupredict-AI — Student Performance Prediction

An AI-powered system that predicts and flags at-risk students using supervised machine learning, helping identify who needs academic support before it's too late.

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=sumitsaxena2716-sys_Edupredict-AI&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=sumitsaxena2716-sys_Edupredict-AI)

---

## 🎯 Overview

Identifying at-risk students early lets institutions step in before performance drops too far. Edupredict-AI uses a supervised ML classification model — trained on student academic and behavioral data — to flag students likely to need extra support, and presents results through a simple web dashboard.

Built as a BCA 4th Semester group project.

---

## ✨ Features

- 🤖 Supervised ML model (Scikit-learn) to classify at-risk students
- 🧹 Data cleaning and feature engineering with Pandas
- 📊 Visual performance dashboard (Chart.js)
- 🗄️ MySQL-backed storage for student records
- 🌐 Flask-based web interface

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Machine Learning | Scikit-learn, Pandas |
| Database | MySQL |
| Frontend | HTML, CSS, Chart.js |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- MySQL Server

### Installation

```bash
# Clone the repository
git clone https://github.com/sumitsaxena2716-sys/Edupredict-AI.git
cd Edupredict-AI

# Install dependencies
pip install -r requirements.txt

# Set up the database
# (import the provided schema/SQL file into your MySQL server)

# Run the application
python app.py
```

Then open `http://localhost:5000` (or the port shown in your terminal) in your browser.

> **Note:** Update the run command and DB setup step above to match your actual entry-point file and schema.


## 🧠 What I Learned

- Cleaning and preparing real-world academic data for machine learning
- Evaluating classification models using standard metrics and iterating on feature selection
- Connecting a trained ML model to a live Flask web app with a MySQL backend

---

## 📄 License

This project is licensed under the MIT License.

---

## 👤 Author

**Sumit Saxena**
[LinkedIn](https://linkedin.com/in/sumit-saxena-54566b310) · [Email](mailto:sumitsaxena2716@gmail.com) · [GitHub](https://github.com/sumitsaxena2716-sys)
