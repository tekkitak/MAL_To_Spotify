import secrets
from time import time
from hashlib import sha256
from urllib.parse import urlencode
import requests as rq
from requests.auth import AuthBase
from typing import Union


class OAuth2(AuthBase):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        oauth_url: str,
        token_url: str,
        method: str,
        scope: Union[str, None] = None,
    ):
        if method is None:  # type: ignore
            self.code_challenge = {"method": None, "expire": -1}
        elif method in ["plain", "S256"]:
            self.code_challenge = {"expire": time() + 600, "method": method}
            self.code_challenge["code"] = self.generate_code_challenge()
        else:
            raise Exception("Invalid code challenge method")

        self.client_data = {
            "state": secrets.token_urlsafe(100)[:128],
            "id": client_id,
            "secret": client_secret,
            "redirect_uri": redirect_uri,
            "url": {"oauth": oauth_url, "token": token_url},
            "scope": scope,
        }

        self.token = {"access": None, "refresh": None, "expire": -1}

    def __call__(self, req: rq.Request):
        if not self.token_valid():
            self.token_from_refresh()

        req.headers["Authorization"] = self.get_Bearer()
        return req

    def generate_code_challenge(self) -> str:
        token = secrets.token_urlsafe(100)[:128]

        if self.code_challenge["method"] == "plain":
            return token
        elif self.code_challenge["method"] == "S256":
            return sha256(token.encode("utf-8")).hexdigest()
        else:
            raise Exception("Cannot call generate_code_challenge() for this method!")

    def challenge_valid(self) -> bool:
        if self.code_challenge["method"] is None:
            return True
        return self.code_challenge.get("expire", 1) > time()

    def renew_challenge(self) -> None:
        self.code_challenge["code"] = self.generate_code_challenge()
        self.code_challenge["expire"] = time() + 600

    def get_auth_url(self) -> str:
        params = {
            "response_type": "code",
            "client_id": self.client_data["id"],
            "redirect_uri": self.client_data["redirect_uri"],
            "state": self.client_data["state"],
        }

        if self.client_data["scope"] is not None:
            params["scope"] = self.client_data["scope"]

        if self.code_challenge["method"] is None:
            if not self.challenge_valid():
                self.renew_challenge()
            params["code_challenge_method"] = self.code_challenge["method"]
            params["code_challenge"] = self.code_challenge["code"]

        return self.client_data["url"]["oauth"] + "?" + urlencode(params)

    def token_from_code(self, code: str):
        params = {
            "client_id": self.client_data["id"],
            "client_secret": self.client_data["secret"],
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.client_data["redirect_uri"],
            "state": self.client_data["state"],
        }
        if self.code_challenge["method"] is not None:
            if not self.challenge_valid():
                self.renew_challenge()
            params["code_challenge_method"] = self.code_challenge["method"]
            params["code_verifier"] = self.code_challenge["code"]

        req = rq.post(self.client_data["url"]["token"], data=params)
        json = req.json()

        if json.get("error", None) is not None:
            raise Exception(req.json()["error"])

        self.token["access"] = json["access_token"]
        self.token["refresh"] = json["refresh_token"]
        self.token["expire"] = time() + json["expires_in"]

    def token_from_refresh(self):
        params = {
            "client_id": self.client_data["id"],
            "client_secret": self.client_data["secret"],
            "refresh_token": self.token["refresh"],
            "grant_type": "refresh_token",
        }

        req = rq.post(self.client_data["url"]["token"], data=params)
        json = req.json()

        if json.get("error", None) is not None:
            raise Exception(req.json()["error"])

        self.token["access"] = json["access_token"]
        self.token["expire"] = time() + json["expires_in"]

    def token_valid(self) -> bool:
        if self.token["expire"] is None or self.token["access"] is None:
            return False
        return self.token["expire"] > time()

    def get_Bearer(self) -> str:
        if self.token["access"] is None:
            raise Exception("No Access Token!\nHint: call token_from_code()")
        if not self.token_valid():
            self.token_from_refresh()
        return "Bearer " + self.token["access"]


def MalOAuth2Builder(client_id: str, client_secret: str, redirect_url: str) -> OAuth2:
    return OAuth2(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_url,
        oauth_url="https://myanimelist.net/v1/oauth2/authorize",
        token_url="https://myanimelist.net/v1/oauth2/token",
        method="plain",
    )

def SpotifyOAuth2Builder(client_id: str, client_secret: str, redirect_url: str) -> OAuth2:
    return OAuth2(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_url,
        oauth_url="https://accounts.spotify.com/authorize",
        token_url="https://accounts.spotify.com/api/token",
        method="S256",
    )
