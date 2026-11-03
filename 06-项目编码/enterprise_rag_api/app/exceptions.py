"""Domain exceptions mapped to unified envelope."""


class AppError(Exception):
    def __init__(self, code: int, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class BadRequest(AppError):
    def __init__(self, message: str = "参数校验失败"):
        super().__init__(40001, message, 400)


class Unauthorized(AppError):
    def __init__(self, message: str = "未登录或令牌无效"):
        super().__init__(40101, message, 401)


class Forbidden(AppError):
    def __init__(self, message: str = "无权限"):
        super().__init__(40301, message, 403)


class NotFound(AppError):
    def __init__(self, message: str = "资源不存在"):
        super().__init__(40401, message, 404)


class Conflict(AppError):
    def __init__(self, message: str = "业务冲突"):
        super().__init__(40901, message, 409)


class RateLimited(AppError):
    def __init__(self, message: str = "请求过于频繁"):
        super().__init__(42901, message, 429)
