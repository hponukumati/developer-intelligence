from app.main import app


def test_cors_permits_local_ui_put_requests_without_a_trailing_origin_slash():
    middleware = next(item for item in app.user_middleware if item.cls.__name__ == "CORSMiddleware")

    assert "PUT" in middleware.kwargs["allow_methods"]
    assert "http://localhost:3000" in middleware.kwargs["allow_origins"]
    assert all(not origin.endswith("/") for origin in middleware.kwargs["allow_origins"])
