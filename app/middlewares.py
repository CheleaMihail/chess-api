from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from app.services import auth


class TokenAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.public_paths = [
            "/auth/login/",
            "/auth/register/",
            "/users",
        ]

    async def dispatch(self, request: Request, call_next):
        try:
            # Skip token check for public routes
            if any(request.url.path.startswith(prefix) for prefix in self.public_paths):
                return await call_next(request)

            # Check for Authorization header
            authorization: str = request.headers.get("Authorization")

            if authorization is None:
                raise HTTPException(
                    status_code=401, detail="Authorization header missing"
                )

            token_type, token = authorization.split(" ")

            # Verify the token
            token_data = auth.verify_access_token(token)

            if not token_data:
                raise HTTPException(status_code=401, detail="Unauthorized")

            # Store user data (e.g., user id) in request.state
            request.state.user_id = token_data.id
            request.state.username = token_data.username

        except HTTPException as http_exc:
            # Directly return 401 Unauthorized if we have HTTPException
            return Response(
                content=f"{http_exc.detail}", status_code=http_exc.status_code
            )
        except Exception as exc:
            # Catch all other exceptions and return generic 401
            return Response(content="Unauthorized", status_code=401)

        # Continue with the request if no exception occurred
        response = await call_next(request)
        return response
