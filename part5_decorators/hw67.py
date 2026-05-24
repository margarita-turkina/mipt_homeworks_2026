import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import wraps
from typing import Any, NoReturn, ParamSpec, TypeVar
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
INVALID_TRIGGERS_ON = "Breaker triggers_on must be an Exception subclass!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."

P = ParamSpec("P")
R = TypeVar("R")


def _is_positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_valid_exception_cls(value: object) -> bool:
    return isinstance(value, type) and issubclass(value, Exception)


def _collect_validation_errors(
    critical_count: int,
    time_to_recover: int,
    triggers_on: object,
) -> list[ValueError]:
    errors: list[ValueError] = []

    if not _is_positive_int(critical_count):
        errors.append(ValueError(INVALID_CRITICAL_COUNT))

    if not _is_positive_int(time_to_recover):
        errors.append(ValueError(INVALID_RECOVERY_TIME))

    if not _is_valid_exception_cls(triggers_on):
        errors.append(ValueError(INVALID_TRIGGERS_ON))

    return errors


def _resolve_triggers_on(triggers_on: type[Exception] | None) -> type[Exception]:
    if triggers_on is None:
        return Exception
    return triggers_on


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


@dataclass
class _BreakerState:
    failure_count: int = 0
    block_time: datetime | None = None


def _raise_if_blocked(state: _BreakerState, time_to_recover: int, func_name: str) -> None:
    if state.block_time is None:
        return
    recovery_delta = timedelta(seconds=time_to_recover)
    if datetime.now(UTC) - state.block_time < recovery_delta:
        raise BreakerError(TOO_MUCH, func_name=func_name, block_time=state.block_time)
    state.block_time = None
    state.failure_count = 0


def _process_failure(
    exc: Exception,
    state: _BreakerState,
    triggers_on: type[Exception],
    critical_count: int,
    func_name: str,
) -> NoReturn:
    if not isinstance(exc, triggers_on):
        raise exc
    state.failure_count += 1
    if state.failure_count < critical_count:
        raise exc
    state.block_time = datetime.now(UTC)
    raise BreakerError(TOO_MUCH, func_name=func_name, block_time=state.block_time) from exc


class CircuitBreaker:
    def __init__(
        self,
        critical_count: int = 5,
        time_to_recover: int = 30,
        triggers_on: type[Exception] | None = None,
    ) -> None:
        triggers_for_validation = Exception if triggers_on is None else triggers_on
        validation_errors = _collect_validation_errors(
            critical_count,
            time_to_recover,
            triggers_for_validation,
        )
        if validation_errors:
            raise ExceptionGroup(VALIDATIONS_FAILED, validation_errors)

        self.critical_count = critical_count
        self.time_to_recover = time_to_recover
        self.triggers_on = _resolve_triggers_on(triggers_on)

    def __call__(self, func: Callable[P, R]) -> Callable[P, R]:
        func_name = f"{func.__module__}.{func.__name__}"
        state = _BreakerState()

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            _raise_if_blocked(state, self.time_to_recover, func_name)
            try:
                result = func(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001
                _process_failure(exc, state, self.triggers_on, self.critical_count, func_name)
            else:
                state.failure_count = 0
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
