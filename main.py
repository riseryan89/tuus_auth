from dataclasses import asdict

import uvicorn
from fastapi import FastAPI
from fastapi.security import APIKeyHeader
from starlette.middleware.cors import CORSMiddleware

from db.conn import db
from settings import env
from api.common import routes as c_r

API_KEY_HEADER = APIKeyHeader(name="Authorization", auto_error=False)


def create_app():
    """
    앱 함수 실행
    :return:
    """
    c = env()
    app = FastAPI()
    conf_dict = asdict(c)
    print(conf_dict)
    db.init_app(app, **conf_dict)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=c.ALLOW_SITE,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(c_r.router)
    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
