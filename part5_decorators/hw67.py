import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."

P = ParamSpec("P")
R = TypeVar("R")


def _is_positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


class BreakerError(Exception):
    def __init__(
        self,
        message: str = TOO_MUCH,
        *,
        func_name: str | None = None,
        block_time: datetime | None = None,
    ) -> None:
        super().__init__(message)
        self.func_name = func_name
        self.block_time = block_time


class CircuitBreaker:
    def __init__(
        self,
        critical_count: int = 5,
        time_to_recover: int = 30,
        triggers_on: type[Exception] | None = None,
    ) -> None:
        validation_errors: list[ValueError] = []
        if not _is_positive_int(critical_count):
            validation_errors.append(ValueError(INVALID_CRITICAL_COUNT))
        if not _is_positive_int(time_to_recover):
            validation_errors.append(ValueError(INVALID_RECOVERY_TIME))
        if validation_errors:
            raise ExceptionGroup(VALIDATIONS_FAILED, validation_errors)

        self.critical_count = critical_count
        self.time_to_recover = time_to_recover
        self.triggers_on = triggers_on if triggers_on is not None else Exception

    def __call__(self, func: Callable[P, R]) -> Callable[P, R]:
        func_name = f"{func.__module__}.{func.__name__}"
        failure_count = 0
        block_time: datetime | None = None

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            nonlocal failure_count, block_time

            if block_time is not None:
                if datetime.now(UTC) - block_time < timedelta(seconds=self.time_to_recover):
                    raise BreakerError(
                        TOO_MUCH,
                        func_name=func_name,
                        block_time=block_time,
                    )
                block_time = None
                failure_count = 0

            try:
                result = func(*args, **kwargs)
            except Exception as exc:
                if isinstance(exc, self.triggers_on):
                    failure_count += 1
                    if failure_count >= self.critical_count:
                        block_time = datetime.now(UTC)
                        raise BreakerError(
                            TOO_MUCH,
                            func_name=func_name,
                            block_time=block_time,
                        ) from exc
                raise
            else:
                failure_count = 0
                return result

        return wrapper


circuit_breaker = CircuitBreaker(5, 30, Exception)


def get_comments(post_id: int) -> Any:
    """
    Получает комментарии к посту

    Args:
        post_id (int): Идентификатор поста

    Returns:
        list[dict[int | str]]: Список комментариев
    """
    response = urlopen(f"https://jsonplaceholder.typicode.com/comments?postId={post_id}")
    return json.loads(response.read())


if __name__ == "__main__":
    comments = get_comments(1)
