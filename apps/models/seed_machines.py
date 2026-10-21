# seed_machines.py
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from apps.models.db_models import SessionLocal, Machine

session = SessionLocal()
machines = [
    Machine(machine_code="M-001", name="Machine1", site="Plant A", area="N/A", equipment_type="Motor", supplier="N/A", status="online", opcua_node="Machine1"),
    Machine(machine_code="M-002", name="Machine2", site="Plant A", area="N/A", equipment_type="Motor", supplier="N/A", status="online", opcua_node="Machine2"),
    Machine(machine_code="M-003", name="Machine3", site="Plant A", area="N/A", equipment_type="Motor", supplier="N/A", status="online", opcua_node="Machine3"),
]
session.add_all(machines)
session.commit()
print("Seeded 3 machines.")
session.close()