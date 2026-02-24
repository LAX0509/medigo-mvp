from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime
from backend.database import get_db_connection
from backend.user_router import get_current_user_id  # ya existe en tu user_router
from backend.database import get_db_connection

router = APIRouter()

class PrescriptionIn(BaseModel):
    medication_name: str
    dose: Optional[str] = None
    route: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    quantity: Optional[str] = None
    instructions: Optional[str] = None

class OrderIn(BaseModel):
    type: Literal['lab','imaging','procedure','referral']
    name: str
    priority: Optional[Literal['normal','prioritary','urgent']] = 'normal'
    notes: Optional[str] = None
    scheduled_date: Optional[str] = None   # "YYYY-MM-DDTHH:MM"

class CompleteAppointmentIn(BaseModel):
    notes: Optional[str] = None
    prescriptions: List[PrescriptionIn] = []
    orders: List[OrderIn] = []

def _user_role(cur, user_id: int):
    cur.execute("SELECT role FROM users WHERE id=%s", (user_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return row["role"]

def _ensure_doctor_owns_appointment(cur, doctor_id: int, appointment_id: int):
    cur.execute("SELECT doctor_id, status FROM appointments WHERE id=%s", (appointment_id,))
    a = cur.fetchone()
    if not a:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    if a["doctor_id"] != doctor_id:
        raise HTTPException(status_code=403, detail="No autorizado para modificar esta cita")
    return a

@router.post("/appointments/{appointment_id}/complete")
def complete_appointment(appointment_id: int,
                         payload: CompleteAppointmentIn,
                         user_id: int = Depends(get_current_user_id)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")
    try:
        cur = conn.cursor(dictionary=True)
        role = _user_role(cur, user_id)
        if role != "doctor":
            raise HTTPException(status_code=403, detail="Solo los doctores pueden completar citas")

        a = _ensure_doctor_owns_appointment(cur, user_id, appointment_id)

        if payload.notes:
            cur.execute(
                "INSERT INTO consult_notes (appointment_id, note) VALUES (%s, %s)",
                (appointment_id, payload.notes)
            )

        for p in payload.prescriptions:
            cur.execute("""
                INSERT INTO prescriptions
                (appointment_id, medication_name, dose, route, frequency, duration, quantity, instructions)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (appointment_id, p.medication_name, p.dose, p.route, p.frequency, p.duration, p.quantity, p.instructions))

        for o in payload.orders:
            dt = None
            if o.scheduled_date:
                iso = o.scheduled_date.replace("T"," ")
                if len(iso) == 16: iso += ":00"
                dt = datetime.strptime(iso, "%Y-%m-%d %H:%M:%S")
            cur.execute("""
                INSERT INTO orders
                (appointment_id, type, name, priority, notes, scheduled_date)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (appointment_id, o.type, o.name, o.priority or 'normal', o.notes, dt))

        if a["status"] != "completed":
            cur.execute("UPDATE appointments SET status='completed' WHERE id=%s", (appointment_id,))

        conn.commit()
        return {"msg": "Cita completada y registrada"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al completar la cita: {str(e)}")
    finally:
        try: cur.close()
        except: pass
        conn.close()

@router.get("/appointments/{appointment_id}/summary")
def appointment_summary(appointment_id: int, user_id: int = Depends(get_current_user_id)):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT a.*, p.full_name AS patient_name, d.full_name AS doctor_name, d.specialty
            FROM appointments a
            JOIN users p ON p.id=a.patient_id
            JOIN users d ON d.id=a.doctor_id
            WHERE a.id=%s
        """, (appointment_id,))
        a = cur.fetchone()
        if not a:
            raise HTTPException(status_code=404, detail="Cita no encontrada")
        if user_id not in (a["patient_id"], a["doctor_id"]):
            raise HTTPException(status_code=403, detail="No autorizado")

        from datetime import datetime  # arriba ya está importado

        # Prescriptions
        cur.execute("SELECT * FROM prescriptions WHERE appointment_id=%s ORDER BY id", (appointment_id,))
        prescriptions = cur.fetchall()
        for p in prescriptions:
            if isinstance(p.get("created_at"), datetime):
                p["created_at"] = p["created_at"].strftime("%Y-%m-%d %H:%M:%S")

        # Orders
        cur.execute("SELECT * FROM orders WHERE appointment_id=%s ORDER BY id", (appointment_id,))
        orders = cur.fetchall()
        for o in orders:
            if isinstance(o.get("scheduled_date"), datetime):
               o["scheduled_date"] = o["scheduled_date"].strftime("%Y-%m-%d %H:%M:%S")
            if isinstance(o.get("created_at"), datetime):
               o["created_at"] = o["created_at"].strftime("%Y-%m-%d %H:%M:%S")

        # Nota (si existe)
        cur.execute("SELECT note, created_at FROM consult_notes WHERE appointment_id=%s ORDER BY id DESC LIMIT 1", (appointment_id,))
        note = cur.fetchone()
        if note and isinstance(note.get("created_at"), datetime):
            note["created_at"] = note["created_at"].strftime("%Y-%m-%d %H:%M:%S")


        return {
            "appointment": {
                "id": a["id"],
                "appointment_date": a["appointment_date"].strftime("%Y-%m-%d %H:%M:%S"),
                "reason": a["reason"],
                "status": a["status"],
                "patient_name": a["patient_name"],
                "doctor_name": a["doctor_name"],
                "specialty": a["specialty"],
            },
            "note": note,
            "prescriptions": prescriptions,
            "orders": orders
        }
    

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener detalle: {str(e)}")
    finally:
        try: cur.close()
        except: pass
        conn.close()

@router.put("/appointments/{appointment_id}/cancel")
def cancel_appointment(appointment_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verificar si la cita existe
    cursor.execute("SELECT status FROM appointments WHERE id = %s", (appointment_id,))
    appointment = cursor.fetchone()
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    # Verificar si ya está cancelada o completada
    if appointment[0] in ("cancelled", "completed"):
        raise HTTPException(status_code=400, detail="La cita no puede cancelarse")

    # Actualizar estado
    cursor.execute("UPDATE appointments SET status = 'cancelled' WHERE id = %s", (appointment_id,))
    conn.commit()

    return {"message": "Cita cancelada correctamente"}
