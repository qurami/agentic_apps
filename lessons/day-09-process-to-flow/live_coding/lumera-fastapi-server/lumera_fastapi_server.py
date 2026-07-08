import hmac
import os

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel

app = FastAPI(title="Banca Lumera core-banking mock")

API_TOKEN = os.getenv("CORE_BANKING_TOKEN")

if not API_TOKEN:
    raise RuntimeError("CORE_BANKING_TOKEN environment variable is not set")


def verify_token(authorization: str | None = Header(default=None)) -> None:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )

    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Expected: Authorization: Bearer <token>",
        )

    if not hmac.compare_digest(token, API_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


@app.get("/health")
def health():
    # Public endpoint
    return {"status": "ok"}


BALANCES = {
    "checking": 1250.00,
    "savings": 2087.50,
}


@app.get("/v1/balance", dependencies=[Depends(verify_token)])
def balance(account_type: str):
    if account_type not in BALANCES:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown account type: {account_type}",
        )
    return {"account_type": account_type, "balance": BALANCES[account_type]}


class AppointmentRequest(BaseModel):
    customer_id: str
    branch_city: str
    topic: str
    preferred_time: str


APPOINTMENTS: list[dict] = []


@app.post(
    "/v1/appointments",
    dependencies=[Depends(verify_token)],
    status_code=status.HTTP_201_CREATED,
)
def create_appointment(request: AppointmentRequest):
    reference = f"LUM-{len(APPOINTMENTS) + 1:04d}"
    APPOINTMENTS.append({**request.model_dump(), "reference": reference})
    return {"reference": reference, "status": "confirmed"}


# The demo one-time code accepted by the identity check.
DEMO_SECURITY_CODE = "123456"


class VerificationRequest(BaseModel):
    customer_id: str
    security_code: str


@app.post("/v1/auth/verify", dependencies=[Depends(verify_token)])
def verify_identity(request: VerificationRequest):
    verified = hmac.compare_digest(request.security_code, DEMO_SECURITY_CODE)
    return {"customer_id": request.customer_id, "verified": verified}


class TransferRequest(BaseModel):
    customer_id: str
    recipient_name: str
    recipient_iban: str
    amount: float


TRANSFERS: list[dict] = []


@app.post(
    "/v1/transfers",
    dependencies=[Depends(verify_token)],
    status_code=status.HTTP_201_CREATED,
)
def create_transfer(request: TransferRequest):
    # Mock simplification: every transfer leaves the checking account,
    # and overdrafts are allowed.
    BALANCES["checking"] -= request.amount
    transfer_id = f"TRF-{len(TRANSFERS) + 1:04d}"
    TRANSFERS.append({**request.model_dump(), "transfer_id": transfer_id})
    return {"transfer_id": transfer_id, "status": "executed"}
