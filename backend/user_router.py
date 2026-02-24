from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from backend.database import get_db_connection
import bcrypt

router = APIRouter()

# ========== MODELOS ==========
class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: str                    # "patient" o "doctor"
    specialty: Optional[str] = None  # solo aplica si role = doctor

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class AppointmentCreate(BaseModel):
    doctor_id: int
    appointment_date: str        # "YYYY-MM-DDTHH:MM" (input datetime-local)
    reason: str

# ========== HELPERS ==========
def hash_password(plain: str) -> str:
    """Devuelve el hash bcrypt como string (utf-8) para guardar en la DB."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    """Verifica una contraseña en texto plano contra un hash almacenado (utf-8)."""
    # Asegurar que 'hashed' sea str (por si viene como bytes/BLOB de MySQL)
    if isinstance(hashed, (bytes, bytearray)):
        hashed = hashed.decode("utf-8", errors="ignore")
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

def get_current_user_id(authorization: str = Header(None)) -> int:
    """
    Lee el token desde el header Authorization.
    Acepta 'Bearer 123' o '123'. En este ejemplo: token = id del usuario.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Falta encabezado Authorization")
    token = authorization.replace("Bearer", "").strip()
    try:
        return int(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Token inválido")

# ========== ENDPOINTS ==========

@router.post("/register")
def register_user(user: UserRegister):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")

    # Si no es doctor, specialty debe quedar en NULL (None)
    if user.role not in ("patient", "doctor"):
        raise HTTPException(status_code=400, detail="Rol inválido")
    if user.role != "doctor":
        user.specialty = None

    try:
        cur = conn.cursor(dictionary=True)

        # ¿correo ya existe?
        cur.execute("SELECT id FROM users WHERE email=%s", (user.email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="El correo ya está registrado")

        pwd_hash = hash_password(user.password)

        cur.execute(
            """
            INSERT INTO users (full_name, email, password_hash, role, specialty)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user.full_name, user.email, pwd_hash, user.role, user.specialty),
        )
        conn.commit()

        # Autologin simple: devolvemos datos mínimos para que el frontend haga login aparte si quiere
        return {"msg": "Usuario creado correctamente"}
    except Exception as e:
        # Puedes loguear e en consola si quieres más detalle
        raise HTTPException(status_code=500, detail=f"Error al registrar: {str(e)}")
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()

@router.post("/login")
def login(user: UserLogin):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")

    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT id, full_name, email, password_hash, role, specialty FROM users WHERE email=%s",
            (user.email,)
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        hashed = row["password_hash"]  # puede venir como bytes (BLOB) o str (VARCHAR)
        if not verify_password(user.password, hashed):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        # Token de ejemplo = id (suficiente para demo/POC).
        return {
            "token": str(row["id"]),
            "user_id": row["id"],
            "full_name": row["full_name"],
            "email": row["email"],
            "role": row["role"],
            "specialty": row["specialty"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en login: {str(e)}")
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()

@router.get("/doctors")
def get_doctors():
    """
    Lista de doctores (para llenar el select).
    Formato que espera el frontend: { "doctors": [ {user_id, full_name, specialty}, ... ] }
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")

    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id AS user_id, full_name, email, specialty FROM users WHERE role='doctor'")
        doctors = cur.fetchall()
        return {"doctors": doctors}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar doctores: {str(e)}")
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()

@router.post("/appointments")
def create_appointment(appointment: AppointmentCreate, user_id: int = Depends(get_current_user_id)):
    """
    Crea una cita. Requiere header Authorization con el token (id del usuario).
    Acepta fecha "YYYY-MM-DDTHH:MM" (agregamos :00 si no envían segundos).
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")

    try:
        cur = conn.cursor(dictionary=True)

        # Validar que el doctor exista
        cur.execute("SELECT id FROM users WHERE id=%s AND role='doctor'", (appointment.doctor_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=400, detail="Doctor no encontrado")

        # Parse fecha
        iso = appointment.appointment_date.replace("T", " ")
        if len(iso) == 16:  # YYYY-MM-DD HH:MM
            iso += ":00"
        try:
            dt = datetime.strptime(iso, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha/hora inválido")

        cur.execute(
            """
            INSERT INTO appointments (patient_id, doctor_id, appointment_date, reason, status)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, appointment.doctor_id, dt, appointment.reason, "scheduled"),
        )
        conn.commit()
        return {"msg": "Cita creada correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear la cita: {str(e)}")
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()

@router.get("/appointments/history")
def get_appointment_history(user_id: int = Depends(get_current_user_id)):
    """
    Historial de citas. Si el usuario es paciente -> ve sus citas con los doctores.
    Si es doctor -> ve sus citas con pacientes.
    Respuesta que espera el frontend: { "history": [...] }
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")

    try:
        cur = conn.cursor(dictionary=True)

        # Saber rol del usuario
        cur.execute("SELECT role FROM users WHERE id=%s", (user_id,))
        u = cur.fetchone()
        if not u:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        if u["role"] == "patient":
            cur.execute(
                """
                SELECT a.id, a.appointment_date, a.reason, a.status,
                       d.full_name AS doctor_name, d.email AS doctor_email, d.specialty
                FROM appointments a
                JOIN users d ON d.id = a.doctor_id
                WHERE a.patient_id = %s
                ORDER BY a.appointment_date DESC
                """,
                (user_id,),
            )
            rows = cur.fetchall()
            history = [
                {
                    "id": r["id"],
                    "appointment_date": r["appointment_date"].strftime("%Y-%m-%d %H:%M:%S"),
                    "reason": r["reason"],
                    "status": r["status"],
                    "doctor_name": r["doctor_name"],
                    "doctor_email": r["doctor_email"],
                    "specialty": r["specialty"],
                }
                for r in rows
            ]
            return {"history": history}

        # role = doctor
        cur.execute(
            """
            SELECT a.id, a.appointment_date, a.reason, a.status,
                   p.full_name AS patient_name, p.email AS patient_email
            FROM appointments a
            JOIN users p ON p.id = a.patient_id
            WHERE a.doctor_id = %s
            ORDER BY a.appointment_date DESC
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        history = [
            {
                "id": r["id"],
                "appointment_date": r["appointment_date"].strftime("%Y-%m-%d %H:%M:%S"),
                "reason": r["reason"],
                "status": r["status"],
                "patient_name": r["patient_name"],
                "patient_email": r["patient_email"],
            }
            for r in rows
        ]
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener historial: {str(e)}")
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()

