"""Oauth 2.0 Authorization Code Grant flow implementation that can be used as authorization for requests library"""
import secrets
from time import time
from hashlib import sha256
from base64 import b64encode as b64e
from urllib.parse import urlencode
import requests as rq
from requests.auth import AuthBase
from typing import Optional


class OAuth2(AuthBase):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        oauth_url: str,
        token_url: str,
        method: Optional[str],
        scope: Optional[str] = None,
    ):
        """
        OAuth2 class for handling OAuth2.0 Authorization Code Grant flow

        Params:
            client_id: str - Client ID
            client_secret: str - Client Secret
            redirect_uri: str - Redirect URI that will be called after Authorization
            oauth_url: str - OAuth2.0 Website authorization URL
            token_url: str - OAuth2.0 Website token URL
            method: Optional[str] - Code Challenge Method
                None - No Code Challenge
                'plain' - there is only token sent as code_challenge and code_verifier
                'S256' - there is SHA256 hash of code_verifier sent as code_challenge
            scope: Optional[str] - Scope for the OAuth2.0

        Return:
            OAuth2 object that you can call to get the Bearer Token
        """
        if method is None:  # type: ignore
            self.code_challenge = {"method": None, "expire": -1}
        elif method in ["plain", "S256"]:
            self.code_challenge = {"expire": time() + 600, "method": method}
            self.code_challenge["code"] = self.__generate_code_challenge()
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
        """Add Authorization header to the request"""
        if not self.__token_valid():
            self.__token_from_refresh()

        req.headers["Authorization"] = self.get_Bearer()
        return req

    def __generate_code_challenge(self) -> str:
        """Generate code challenge for the code verifier"""
        self.code_challenge["code_verifier"] = secrets.token_urlsafe(100)[:128]

        if self.code_challenge["method"] == "plain":
            return self.code_challenge["code_verifier"]
        elif self.code_challenge["method"] == "S256":
            hashed = sha256(self.code_challenge["code_verifier"].encode("utf-8")).digest()
            encoded = b64e(hashed).decode("utf-8").replace("=", "").replace("+", "-").replace("/", "_")
            return encoded
        else:
            raise Exception("Cannot call generate_code_challenge() for this method!")

    def __challenge_valid(self) -> bool:
        """Checks if the code challenge is still valid"""
        if self.code_challenge["method"] is None:
            return True
        return self.code_challenge.get("expire", 1) > time()

    def __renew_challenge(self) -> None:
        """Renews the code challenge"""
        self.code_challenge["code"] = self.__generate_code_challenge()
        self.code_challenge["expire"] = time() + 600

    def get_auth_url(self) -> str:
        """Get the URL for the OAuth2.0 Authorization
        Return:
            str - url
        """
        params = {
            "response_type": "code",
            "client_id": self.client_data["id"],
            "redirect_uri": self.client_data["redirect_uri"],
            "state": self.client_data["state"],
        }

        if self.client_data["scope"] is not None:
            params["scope"] = self.client_data["scope"]

        if self.code_challenge["method"] is not None:
            if not self.__challenge_valid():
                self.__renew_challenge()
            params["code_challenge_method"] = self.code_challenge["method"]
            params["code_challenge"] = self.code_challenge["code"]

        return self.client_data["url"]["oauth"] + "?" + urlencode(params)

    def token_from_code(self, code: str) -> None:
        """Gets the token from code returned by the authorization server

        Params:
            code: str - Code returned by the authorization server

        Return:
            None
        """
        params = {
            "client_id": self.client_data["id"],
            "client_secret": self.client_data["secret"],
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.client_data["redirect_uri"],
            "state": self.client_data["state"],
        }
        if self.code_challenge["method"] is not None:
            if not self.__challenge_valid():
                self.__renew_challenge()
            params["code_challenge_method"] = self.code_challenge["method"]
            params["code_verifier"] = self.code_challenge["code_verifier"]

        req = rq.post(self.client_data["url"]["token"], data=params)
        json = req.json()

        if json.get("error", None) is not None:
            raise Exception(req.json())

        self.token["access"] = json["access_token"]
        self.token["refresh"] = json["refresh_token"]
        self.token["expire"] = time() + json["expires_in"]

    def __token_from_refresh(self) -> None:
        """Gets the token from refresh token"""
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

    def __token_valid(self) -> bool:
        """Internal function to check if the token is still valid"""
        if self.token["expire"] is None or self.token["access"] is None:
            return False
        return self.token["expire"] > time()

    def get_Bearer(self) -> str:
        """Get the Bearer token for the Authorization header"""
        if self.token["access"] is None:
            raise Exception("No Access Token!\nHint: call token_from_code()")
        if not self.__token_valid():
            self.__token_from_refresh()
        return "Bearer " + self.token["access"]


def MalOAuth2Builder(client_id: str, client_secret: str, redirect_url: str) -> OAuth2:
    """OAuth2 Builder for MyAnimeList"""
    return OAuth2(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_url,
        oauth_url="https://myanimelist.net/v1/oauth2/authorize",
        token_url="https://myanimelist.net/v1/oauth2/token",
        method="plain",
    )


def SpotifyOAuth2Builder(client_id: str, client_secret: str, redirect_url: str) -> OAuth2:
    """OAuth2 Builder for Spotify"""
    return OAuth2(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_url,
        oauth_url="https://accounts.spotify.com/authorize",
        token_url="https://accounts.spotify.com/api/token",
        method="S256",
        scope="playlist-read-private", # Appended to default scope
    )
