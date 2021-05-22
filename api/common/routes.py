from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.responses import Response

from db.conn import db
from db.models import Users

router = APIRouter()


@router.get("/")
async def index(db: Session = Depends(db.session)):
    """
    ELB 상태 체크용 API
    :return:
    """
    a = db.query(Users).all()
    print(a)
    current_time = datetime.utcnow()
    return Response(f"Notification API (UTC: {current_time.strftime('%Y.%m.%d %H:%M:%S')})")

