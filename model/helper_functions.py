import requests as rq
from flask import session, redirect, url_for
from os import getenv
from datetime import datetime, timedelta
from base64 import b64encode as b64en
from typing import Union, cast
from werkzeug.wrappers.response import Response


def exec_request(
    url, headers=None, params=None, data=None, method="GET", auth=True
) -> Union[Response, rq.Response]:
    if auth:
        if session.get("spotify_access_token", False) is False:
            # print('redirected for no token')
            return redirect(url_for("index"))
        if (
            session.get("token_expiration_time", datetime.now() + timedelta(seconds=1))
            < datetime.now()
        ):
            # print('redirected for token expiration')
            refresh_auth()

    i: int = 0
    while True:
        try:
            res = rq.request(
                method, url, headers=headers, params=params, data=data, timeout=2
            )
        except Exception:
            print("Failed to connect to spotify, retrying...")
            if i > 10:
                raise Exception("Failed to connect to spotify after 10 retries")
            i += 1
            continue
        break

    if res.status_code == 401:
        print("401 error")
        print(res.text)
        raise Exception(res.json()["error"])
    return res


def refresh_auth() -> None:
    url = "https://accounts.spotify.com/api/token"
    body = {
        "grant_type": "refresh_token",
        "refresh_token": session.get("spotify_refresh_token", False),
    }
    assert (
        getenv("SPOT_ID") is not None and getenv("SPOT_SECRET") is not None
    ), "SPOT_ID or SPOT_SECRET not set"
    spot_id: str = cast(str, getenv("SPOT_ID"))
    spot_secret: str = cast(str, getenv("SPOT_SECRET"))
    headers = {
        "Authorization": "Basic " + encode_base64(spot_id + ":" + spot_secret),
    }
    req: dict = cast(
        rq.Response,
        exec_request(url, headers=headers, data=body, method="POST", auth=False),
    ).json()
    session["spotify_access_token"] = req["access_token"]
    session["token_expiration_time"] = datetime.now() + timedelta(
        seconds=req["expires_in"]
    )


def encode_base64(string: str) -> str:
    return b64en(string.encode("ascii")).decode("ascii")
