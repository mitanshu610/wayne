from pydantic import BaseModel, Field

class CreatePaygoOrderSchema(BaseModel):
    plan_id: int
