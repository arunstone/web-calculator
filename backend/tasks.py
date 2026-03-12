from sqlalchemy import select

from backend.celery_app import celery_app
from backend.database import SessionLocal
from backend.models import CalculationRequest


def perform_calculation(operation: str, operand_a: float, operand_b: float) -> float:
    if operation == "add":
        return operand_a + operand_b
    if operation == "subtract":
        return operand_a - operand_b
    if operation == "multiply":
        return operand_a * operand_b
    if operation == "divide":
        if operand_b == 0:
            raise ValueError("Cannot divide by zero")
        return operand_a / operand_b
    raise ValueError(f"Unsupported operation: {operation}")


@celery_app.task(name="backend.tasks.process_calculation")
def process_calculation(request_id: int) -> dict[str, float | int]:
    db = SessionLocal()
    try:
        calculation = db.execute(
            select(CalculationRequest).where(CalculationRequest.id == request_id)
        ).scalar_one()
        try:
            result = perform_calculation(calculation.operation, calculation.operand_a, calculation.operand_b)
            calculation.result = result
            calculation.status = "completed"
            calculation.error_message = None
        except Exception as exc:
            calculation.status = "failed"
            calculation.error_message = str(exc)
            raise
        finally:
            db.add(calculation)
            db.commit()
            db.refresh(calculation)
        return {"request_id": calculation.id, "result": calculation.result or 0}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
