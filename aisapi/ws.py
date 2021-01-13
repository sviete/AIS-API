"""
Python wrapper package for the AIS API.

This code is released under the terms of the MIT license. See the LICENSE
file for more details.
"""
import asyncio
import logging
import socket
import aiohttp
import async_timeout
from .const import (
    AIS_WS_TTS_URL,
    AIS_WS_COMMAND_URL,
    AIS_WS_AUDIO_STATUS_URL,
    AIS_WS_AUDIO_TYPE_URL,
    AIS_WS_AUDIO_NAME_URL,
    AIS_WS_AUDIOBOOKS_URL,
    AIS_WS_TUNE_IN_URL,
)

_LOGGER = logging.getLogger(__name__)


class AisWebService(object):
    """A class for the AIS WS API."""

    def __init__(self, loop, session, ais_host):
        """Initialize the class."""
        self._loop = asyncio.get_event_loop()
        self._session = session
        self._ais_ws_url = ais_host
        if not self._ais_ws_url.startswith("http"):
            self._ais_ws_url = "http://" + self._ais_ws_url
        if not self._ais_ws_url.endswith(":8122"):
            self._ais_ws_url = self._ais_ws_url + ":8122"
        self._gate_info = None
        self._api_key = None
        self._headers = None
        self._audio_info = None
        self._audiobooks_lib = None

    async def get_gate_info(self):
        """Return the information about gate."""
        try:
            async with async_timeout.timeout(8, loop=self._loop):
                response = await self._session.get(self._ais_ws_url)
                result = await response.json()
                try:
                    if response.status == 200:
                        if "gate_id" in result:
                            self._api_key = result.get("gate_id")
                        else:
                            self._api_key = result.get("ais_gate_client_id")
                        if "NetworkSpeed" not in result:
                            result["NetworkSpeed"] = 0
                        self._gate_info = result
                        self._gate_info["ais_id"] = self._api_key
                        self._gate_info["ais_url"] = self._ais_ws_url
                        self._headers = {
                            # No Authorization to work with books and tune in
                            # "Authorization": self._api_key,
                            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, "
                            "like Gecko) Chrome/75.0.3770.100 Safari/537.36"
                        }
                        return self._gate_info
                    else:
                        _LOGGER.error("Error code %s ", response.status)
                except (TypeError, KeyError) as error:
                    _LOGGER.error("Error parsing data from AIS, %s", error)
        except (asyncio.TimeoutError, aiohttp.ClientError, socket.gaierror) as error:
            _LOGGER.error("Error connecting to AIS, %s", error)
        return None

    async def say_it(self, text):
        """Get tracking information."""
        url = AIS_WS_TTS_URL.format(ais_url=self._ais_ws_url, text=text)
        try:
            async with async_timeout.timeout(8, loop=self._loop):
                response = await self._session.get(url, headers=self._headers)
                result = await response.text()
                try:
                    if response.status == 200:
                        return result
                    else:
                        _LOGGER.error("Error code %s ", response.status)
                except (TypeError, KeyError) as error:
                    _LOGGER.error("Error parsing data from AIS, %s", error)
        except (asyncio.TimeoutError, aiohttp.ClientError, socket.gaierror) as error:
            _LOGGER.error("Error connecting to AIS, %s", error)
        return ""

    async def command(self, command, value):
        """Execute command on AI-Speaker."""
        url = AIS_WS_COMMAND_URL.format(ais_url=self._ais_ws_url)
        requests_json = {command: value}
        try:
            async with async_timeout.timeout(8, loop=self._loop):
                response = await self._session.post(
                    url, json=requests_json, headers=self._headers
                )
                result = await response.text()
                try:
                    if response.status == 200:
                        return result
                    else:
                        _LOGGER.error("Error code %s ", response.status)
                except (TypeError, KeyError) as error:
                    _LOGGER.error("Error parsing data from AIS, %s", error)
        except (asyncio.TimeoutError, aiohttp.ClientError, socket.gaierror) as error:
            _LOGGER.error("Error connecting to AIS, %s", error)
        return ""

    async def get_audio_status(self):
        """Get the audio status from AI-Speaker."""
        url = AIS_WS_AUDIO_STATUS_URL.format(ais_url=self._ais_ws_url)
        try:
            async with async_timeout.timeout(8, loop=self._loop):
                response = await self._session.get(url)
                result = await response.json()
                try:
                    if response.status == 200:
                        self._audio_info = result
                    else:
                        _LOGGER.error("Error code %s ", response.status)
                except (TypeError, KeyError) as error:
                    _LOGGER.error("Error parsing data from AIS, %s", error)
        except (asyncio.TimeoutError, aiohttp.ClientError, socket.gaierror) as error:
            _LOGGER.error("Error connecting to AIS, %s", error)
        return self._audio_info

    async def get_audio_type(self, media_content_id):
        if media_content_id == "ais_radio":
            ais_rest_url = AIS_WS_AUDIO_TYPE_URL.format(audio_nature="Radio")
        elif media_content_id == "ais_podcast":
            ais_rest_url = AIS_WS_AUDIO_TYPE_URL.format(audio_nature="Podcast")
        elif media_content_id == "ais_audio_books":
            ais_rest_url = AIS_WS_AUDIOBOOKS_URL
        elif media_content_id == "ais_tunein":
            ais_rest_url = AIS_WS_TUNE_IN_URL
        try:
            async with async_timeout.timeout(10, loop=self._loop):
                response = await self._session.get(ais_rest_url, headers=self._headers)
                if response.status == 200:
                    try:
                        if media_content_id in "ais_tunein":
                            result = await response.text()
                        else:
                            result = await response.json()
                    except (TypeError, KeyError) as error:
                        _LOGGER.error("Error parsing data from AIS, %s", error)
                    return result
                else:
                    _LOGGER.error("Error code %s ", response.status)
        except (asyncio.TimeoutError, aiohttp.ClientError, socket.gaierror) as error:
            _LOGGER.error("Error connecting to AIS, %s", error)
        return None

    async def get_audio_name(self, media_content_id):
        if media_content_id.startswith("ais_radio"):
            ais_rest_url = AIS_WS_AUDIO_NAME_URL.format(
                audio_nature="Radio",
                audio_type=media_content_id.replace("ais_radio/", ""),
            )
        elif media_content_id.startswith("ais_podcast"):
            ais_rest_url = AIS_WS_AUDIO_NAME_URL.format(
                audio_nature="Podcast",
                audio_type=media_content_id.replace("ais_podcast/", ""),
            )
        elif media_content_id.startswith("ais_audio_books"):
            ais_rest_url = media_content_id.split("/", 3)[3] + "?format=json"
        elif media_content_id.startswith("ais_tunein"):
            ais_rest_url = media_content_id.split("/", 3)[3]
        try:
            async with async_timeout.timeout(8, loop=self._loop):
                response = await self._session.get(ais_rest_url, headers=self._headers)

                if media_content_id.startswith("ais_tunein"):
                    result = await response.text()
                else:
                    result = await response.json()
                try:
                    if response.status == 200:
                        return result
                    else:
                        _LOGGER.error("Error code %s ", response.status)
                except (TypeError, KeyError) as error:
                    _LOGGER.error("Error parsing data from AIS, %s", error)
        except (asyncio.TimeoutError, aiohttp.ClientError, socket.gaierror) as error:
            _LOGGER.error("Error connecting to AIS, %s", error)
        return None

    async def get_podcast_tracks(self, media_content_id):
        lookup_url = media_content_id.split("/", 3)[3]
        try:
            async with async_timeout.timeout(8, loop=self._loop):
                response = await self._session.get(lookup_url)
                result = await response.text()
                try:
                    if response.status == 200:
                        return result
                    else:
                        _LOGGER.error("Error code %s ", response.status)
                except (TypeError, KeyError) as error:
                    _LOGGER.error("Error parsing data from AIS, %s", error)
        except (asyncio.TimeoutError, aiohttp.ClientError, socket.gaierror) as error:
            _LOGGER.error("Error connecting to AIS, %s", error)
        return None

    # Get media content id from AIS
    async def get_media_content_id_form_ais(self, media_content_id):
        """Get media content from ais."""
        response_text = media_content_id
        if media_content_id.startswith("ais_tunein"):
            rest_url = media_content_id.split("/", 3)[3]
            ws_resp = await self._session.get(rest_url, timeout=7)
            response_text = await ws_resp.text()
            response_text = response_text.split("\n")[0]
            if response_text.endswith(".pls"):
                ws_resp = await self._session.get(response_text, timeout=7)
                response_text = await ws_resp.text()
                response_text = response_text.split("\n")[1].replace("File1=", "")
            if response_text.startswith("mms:"):
                ws_resp = await self._session.get(
                    response_text.replace("mms:", "http:"), timeout=7
                )
                response_text = await ws_resp.text()
                response_text = response_text.split("\n")[1].replace("Ref1=", "")
        elif media_content_id.startswith("ais_spotify"):
            response_text = media_content_id.replace("ais_spotify/", "")
        return response_text

    @property
    def gate_info(self):
        """Return the gate info."""
        return self._gate_info
