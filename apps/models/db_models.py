from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean, JSON,
    TIMESTAMP, ForeignKey, Text
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

DATABASE_URL = "postgresql://airflow:airflow@localhost:5432/pdm_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default='viewer')  # 'administrator' | 'engineer' | 'viewer'
    active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)


class Machine(Base):
    __tablename__ = 'machines'
    id = Column(Integer, primary_key=True)
    machine_code = Column(String, unique=True, nullable=False)  # e.g. "M-001"
    name = Column(String)                                        # e.g. "Ball Mill Drive"
    site = Column(String)                                        # e.g. "Mine A"
    area = Column(String)                                        # e.g. "Grinding"
    equipment_type = Column(String)                               # e.g. "Motor"
    supplier = Column(String)
    status = Column(String, default='online')                     # 'online' | 'offline' | 'maintenance'
    opcua_node = Column(String)                                    # e.g. "Machine1" (matches OPC-UA object name)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    readings = relationship("SensorReading", back_populates="machine")


class SensorReading(Base):
    __tablename__ = 'sensor_readings'
    id = Column(Integer, primary_key=True)
    machine_id = Column(Integer, ForeignKey('machines.id'), nullable=False)
    timestamp = Column(TIMESTAMP, default=datetime.utcnow)
    features = Column(JSON)
    source = Column(String)              # e.g. "opcua_live_stream", "api_request"
    ingestion_method = Column(String)    # e.g. "opcua", "manual_api"

    machine = relationship("Machine", back_populates="readings")
    prediction = relationship("Prediction", back_populates="reading", uselist=False)


class Prediction(Base):
    __tablename__ = 'predictions'
    id = Column(Integer, primary_key=True)
    reading_id = Column(Integer, ForeignKey('sensor_readings.id'))
    predicted_class = Column(String)
    confidence = Column(Float)
    model_version = Column(String, default='v1')
    top_features = Column(JSON)
    recommendation = Column(Text)  # JSON string of root_causes (as you already store it)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    reading = relationship("SensorReading", back_populates="prediction")
    alerts = relationship("Alert", back_populates="prediction")
    reports = relationship("Report", back_populates="prediction")


class Alert(Base):
    __tablename__ = 'alerts'
    id = Column(Integer, primary_key=True)
    prediction_id = Column(Integer, ForeignKey('predictions.id'))
    machine_id = Column(Integer, ForeignKey('machines.id'))
    severity = Column(String)               # 'high' | 'medium' | 'low'
    state = Column(String, default='open')  # 'open' | 'acknowledged' | 'resolved'
    sent = Column(Boolean, default=False)
    recipient = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    acknowledged_at = Column(TIMESTAMP, nullable=True)
    acknowledged_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    prediction = relationship("Prediction", back_populates="alerts")


class Report(Base):
    __tablename__ = 'reports'
    id = Column(Integer, primary_key=True)
    prediction_id = Column(Integer, ForeignKey('predictions.id'))
    machine_id = Column(Integer, ForeignKey('machines.id'))
    file_path = Column(String)                 # e.g. "reports/2026/08/machine_03_reading_463.pdf"
    generated_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    email_status = Column(String, default='not_sent')  # 'not_sent' | 'sent' | 'failed'
    email_recipient = Column(String, nullable=True)
    version = Column(Integer, default=1)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    prediction = relationship("Prediction", back_populates="reports")


class AuditLog(Base):
    __tablename__ = 'audit_log'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    action = Column(String)       # e.g. "role_changed", "machine_added", "alert_acknowledged"
    details = Column(Text)        # human-readable description
    timestamp = Column(TIMESTAMP, default=datetime.utcnow)