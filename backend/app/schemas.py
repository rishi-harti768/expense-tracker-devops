from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

Category = Literal["FOOD", "TRANSPORT", "BILLS", "OTHER"]

class ExpenseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    amount: float = Field(gt=0)
    category: Category = "OTHER"
    spent_on: date = Field(default_factory=date.today)
    note: str = ""

class ExpenseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    amount: float | None = Field(default=None, gt=0)
    category: Category | None = None
    spent_on: date | None = None
    note: str | None = None

class ExpenseOut(ExpenseCreate):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class StatsOut(BaseModel):
    total: int
    totalAmount: float
    food: float
    transport: float
    bills: float
    other: float
