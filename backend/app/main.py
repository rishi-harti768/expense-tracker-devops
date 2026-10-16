from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from prometheus_fastapi_instrumentator import Instrumentator

from .config import settings
from .db import Base, engine, get_db
from .models import Expense
from .schemas import ExpenseCreate, ExpenseOut, ExpenseUpdate, StatsOut

app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

@app.on_event("startup")
def startup():
    # Production containers run Alembic before Uvicorn; create_all keeps tests self-contained.
    Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"service": settings.app_name, "version": "1.0.0", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "UP"}

@app.get("/ready")
def ready(db: Session = Depends(get_db)):
    db.execute(select(func.count(Expense.id)))
    return {"status": "READY"}

@app.get("/api/expenses", response_model=list[ExpenseOut])
def list_expenses(db: Session = Depends(get_db)):
    return list(db.scalars(select(Expense).order_by(Expense.id.desc())))

@app.get("/api/expenses/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db)):
    rows = db.execute(select(Expense.category, func.count(Expense.id), func.sum(Expense.amount)).group_by(Expense.category)).all()
    sums = {category: float(amount) for category, _, amount in rows}
    return StatsOut(
        total=sum(count for _, count, _ in rows),
        totalAmount=round(sum(sums.values()), 2),
        food=sums.get("FOOD", 0.0),
        transport=sums.get("TRANSPORT", 0.0),
        bills=sums.get("BILLS", 0.0),
        other=sums.get("OTHER", 0.0),
    )

@app.get("/api/expenses/{expense_id}", response_model=ExpenseOut)
def get_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense

@app.post("/api/expenses", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(payload: ExpenseCreate, db: Session = Depends(get_db)):
    expense = Expense(**payload.model_dump())
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense

@app.put("/api/expenses/{expense_id}", response_model=ExpenseOut)
def update_expense(expense_id: int, payload: ExpenseUpdate, db: Session = Depends(get_db)):
    expense = db.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    for key, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(expense, key, value)
    db.commit()
    db.refresh(expense)
    return expense

@app.delete("/api/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(expense)
    db.commit()
