# Explainable AI Platform for Industrial Predictive Maintenance

An end-to-end AI-driven platform for industrial fault diagnosis, combining multi-sensor data acquisition, machine learning, explainable AI, and maintenance decision support.

**Developed during an industrial internship in digitalization and AI.**

## Overview

Industrial equipment generates valuable sensor data that can help identify abnormal operating conditions and potential mechanical faults. However, a fault prediction alone does not necessarily explain why the fault may be occurring or what maintenance action should be considered.

This project addresses that challenge through an integrated predictive maintenance platform that transforms sensor measurements into interpretable diagnostic results, probable root causes, and actionable maintenance recommendations.

The solution combines an OPC-UA-based data acquisition pipeline, machine learning models, SHAP-based explainability, engineering knowledge, and a web application for monitoring and diagnosis.

## Key Features

- **Industrial Data Acquisition:** Sensor data ingestion through OPC-UA using a simulated industrial environment.
- **Feature Engineering:** Statistical feature extraction from multi-channel sensor signals.
- **Machine Learning:** Multiclass fault classification using a custom PyTorch neural network, with Random Forest and XGBoost baselines.
- **Explainable AI:** SHAP-based feature attribution to help interpret model predictions.
- **Diagnostic Reasoning:** Integration of feature interpretation and knowledge-based rules to identify probable root causes and suggest maintenance actions.
- **Web Application:** Dashboard for machine monitoring, diagnostic visualization, and historical records.
- **Automated Reporting:** PDF diagnostic report generation and report archiving.
- **Email Notifications:** Automated email alerts for qualifying non-normal predictions.
- **Data Persistence:** PostgreSQL storage for machine information, readings, predictions, alerts, reports, and users.
- **Access Control:** Authentication and role-based access for administrators, engineers, and technicians.

## System Architecture

The platform follows a modular architecture that separates data acquisition, processing, diagnostic intelligence, explainability, and application delivery.

<img width="1262" height="635" alt="Screenshot 2026-09-24 193850" src="https://github.com/user-attachments/assets/b7511925-4d6b-490a-a482-fdd701272f72" />

**End-to-end workflow:**

1. **Data Acquisition:** Sensor measurements are generated or replayed by the simulator and exposed through an OPC-UA server.
2. **Data Processing:** The ingestion client retrieves sensor values, processes signal windows, and extracts statistical features.
3. **Fault Classification:** The trained model predicts a fault category and associated confidence score.
4. **Explainability and Reasoning:** SHAP identifies influential features, which are interpreted through engineering knowledge and diagnostic rules.
5. **Decision Support:** The system produces a diagnostic explanation, probable root causes, and maintenance recommendations.
6. **Application Integration:** FastAPI connects the diagnostic pipeline to the web interface, database, reporting, and notification services.

## Machine Learning and Explainability

The classification pipeline uses engineered features extracted from eight sensor channels:

- Tachometer
- Underhang axial, radial, and tangential vibration
- Overhang axial, radial, and tangential vibration
- Microphone signal

Statistical features include mean, standard deviation, RMS, skewness, kurtosis, crest factor, form factor, minimum, and maximum.

The diagnostic task covers six operating conditions:

- Normal
- Imbalance
- Horizontal misalignment
- Vertical misalignment
- Underhang bearing fault
- Overhang bearing fault

A custom PyTorch neural network is evaluated alongside Random Forest and XGBoost baselines.

SHAP-based explanations are combined with engineering interpretation and rule-based reasoning to bridge the gap between a model prediction and a maintenance-oriented diagnosis.

**Important distinction:** The classification model predicts the fault category. The explainability and reasoning layers help interpret that prediction and formulate diagnostic recommendations.

## Technology Stack

| Area | Technologies |
|---|---|
| Programming and data processing | Python, NumPy, Pandas |
| Machine Learning | PyTorch, Scikit-learn, XGBoost |
| Explainable AI | SHAP |
| Industrial communication | OPC-UA, asyncua |
| Backend and API | FastAPI |
| Database and ORM | PostgreSQL, SQLAlchemy |
| Frontend | HTML, CSS, JavaScript |
| Language model integration | Ollama, Llama 3.2 |
| PDF reporting | ReportLab |
| Email notifications | Resend |

## Screenshots

The following screenshots demonstrate the application workflow.

### 1. Monitoring Dashboard

<img width="1637" height="906" alt="Screenshot 2026-09-16 160234" src="https://github.com/user-attachments/assets/fe453878-d930-47f9-88e7-dfadba604f5a" />


*Overview of machine monitoring, diagnostic activity, and system status.*

### 2. Explainable Diagnosis

<img width="1671" height="886" alt="Screenshot 2026-09-16 161136" src="https://github.com/user-attachments/assets/4537444e-b6c7-4146-b103-2a6a5a2d5b81" />


*Predicted fault, confidence score, influential features, probable root causes, and maintenance recommendations.*


### 4. Diagnostic Report

<img width="740" height="847" alt="Screenshot 2026-09-22 164300" src="https://github.com/user-attachments/assets/ff4f9cf5-1bbb-4f78-a0c2-5735f91589bd" />


*Example of the generated diagnostic report.*

## Project Structure

```text

predictive-maintenance-diagnosis/
├── apps/
│   ├── api/                  # FastAPI application, routes, schemas, authentication
│   ├── ingestion/            # OPC-UA simulator and ingestion client
│   ├── models/               # ML model, database models, prediction logic
│   ├── pipeline/             # End-to-end diagnostic pipeline
│   ├── explainability/       # SHAP, feature interpretation, root-cause analysis
│   ├── knowledge/            # Fault knowledge base and diagnostic rules
│   ├── services/             # Email notifications and integrations
│   ├── storage/              # Report storage and persistence
│   ├── web/                  # Web routes, templates, CSS, PDF generation
│   └── config.py             # Application configuration
├── src/
│   └── explainability/       # Additional explainability modules
├── notebooks/                # EDA, model training, SHAP, pipeline experiments
├── data/
│   ├── raw/                  # Raw sensor data (not tracked by Git)
│   └── processed/            # Processed datasets (not tracked by Git)
├── storage/
│   └── reports/              # Generated PDF reports (not tracked by Git)
├── docs/
│   ├── architecture/
│   │   └── global_architecture.png
│   └── screenshots/          # Application screenshots
├── tests/                    # Automated tests
├── create_tables.py          # Database initialization
├── test_email.py             # Email integration test
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
├── .gitignore
└── README.md

```

## Getting Started

### Prerequisites

- Python
- Docker Desktop
- PostgreSQL
- A compatible OPC-UA client and server environment
- Ollama, if using the local language-model reformulation feature

### 1. Clone the repository

```bash
git clone https://github.com/Aya949/predictive-maintenance-diagnosis.git
cd predictive-maintenance-diagnosis
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the environment

Configure the database connection and any required API credentials according to the application's configuration.

Keep credentials in environment variables or a local environment file excluded from version control. Never commit API keys, passwords, or private configuration files.

Ensure PostgreSQL is running and the required database schema has been initialized before starting the application.

### 5. Start the OPC-UA simulator

```bash
python apps/ingestion/simulator.py
```

### 6. Start the ingestion pipeline

In a separate terminal:

```bash
python apps/ingestion/ingestion_client.py
```

### 7. Launch the web application

In another terminal:

```bash
uvicorn apps.api.main:app --reload
```

Open the application at:

http://127.0.0.1:8000

**Note:** The simulator and ingestion client are separate processes. Ensure their configuration, database connection, and OPC-UA endpoint are consistent with your local setup.

## Results and Evaluation

The project includes model development and comparison, signal feature engineering, explainability, and integration into an end-to-end diagnostic workflow.

Model performance should be reported using measured evaluation results, including appropriate classification metrics and a clearly defined test split.


## Limitations and Future Work

The current implementation is developed and tested using a simulated OPC-UA environment and a labeled industrial fault dataset. Its performance in a production environment would require validation using real industrial measurements and a wider range of machines and operating conditions.

Potential future improvements include:

- Validation across additional machines and operating conditions.
- Incorporation of temporal patterns for more robust fault diagnosis.
- Continuous monitoring of model performance and data quality.
- Expanded evaluation of diagnostic explanations and maintenance recommendations.
- Deployment to an industrial or cloud infrastructure.

## Author

**Aya**  
Data Engineer

[GitHub](https://github.com/Aya949)

