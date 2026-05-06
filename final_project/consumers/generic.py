"""Generic consumer package to handle requests with token and exceptions"""

import json
import logging

import httpx

from domain.errors.generic import GenericError

__client = httpx.Client(timeout=100)
__async_client = httpx.AsyncClient(timeout=100)


def __pre_request(token: str | None, **kwargs) -> tuple[dict, dict]:
    """Prepare headers and parameters for request."""

    headers: dict = {'Content-Type': 'application/json'}

    if token is not None:
        headers |= {'Authorization': f'Bearer {token}'}

    if 'headers' in kwargs:
        if 'Authorization' in kwargs['headers'] and kwargs['headers']['Authorization'] is None:
            kwargs['headers']['Authorization'] = ''

        headers.update(kwargs['headers'])
        del kwargs['headers']

    if 'data' in kwargs:
        kwargs['data'] = json.dumps(kwargs['data'])

    if 'params' in kwargs and kwargs['params'] is not None:
        for key, value in kwargs['params'].items():
            if isinstance(value, bool):
                kwargs['params'][key] = 'true' if value is True else 'false'

    if 'files' in kwargs:
        del headers['Content-Type']

    return headers, kwargs


def __post_request(res: httpx.Response, kwargs: dict) -> dict:
    """Process response for request."""
    logging.debug('HTTP protocol version: %s', res.http_version)
    if 200 <= res.status_code < 300:
        return res.json()

    message: str = res.text
    try:
        payload = res.json()
        if isinstance(payload, dict) and 'message' in payload:
            message = str(payload['message'])
        else:
            message = json.dumps(payload)
    except ValueError:
        message = res.text

    raise GenericError(status_code=res.status_code, message=message)


def request(token: str | None, **kwargs) -> dict:
    """Requests request with interceptors to handle token and commons exceptions."""

    headers, kwargs = __pre_request(token, **kwargs)
    req = httpx.Request(headers=headers, **kwargs)
    res = __client.send(req)

    return __post_request(res, kwargs)


async def request_async(token: str | None, **kwargs) -> dict | str:
    """Requests request with interceptors to handle token and commons exceptions."""

    headers, kwargs = __pre_request(token, **kwargs)
    req = httpx.Request(headers=headers, **kwargs)
    res = await __async_client.send(req)

    return __post_request(res, kwargs)
