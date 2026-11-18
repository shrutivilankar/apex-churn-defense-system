from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

from src.errors import tmf_error
from src.routes import BASE_PATH, router

app = FastAPI(title="Apex Churn Defense System")
app.include_router(router, prefix=BASE_PATH)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    details = "; ".join(
        f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}" for err in exc.errors()
    )
    return tmf_error(400, "Invalid input", details)
