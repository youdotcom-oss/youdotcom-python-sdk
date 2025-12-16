from .types import Hooks, BeforeRequestHook, BeforeRequestContext
import httpx
from typing import Union


# This file is only ever generated once on the first generation and then is free to be modified.
# Any hooks you wish to add should be registered in the init_hooks function. Feel free to define them
# in this file or in separate files in the hooks folder.

class YDCUserAgentOverrideHook(BeforeRequestHook):
    """Hook that overrides the User-Agent header in all requests with browser fallback."""

    def before_request(self, hook_ctx: BeforeRequestContext, request: httpx.Request) -> Union[httpx.Request, Exception]:
        """
        Override the User-Agent header before the request is sent.

        In browser environments where setting User-Agent may be restricted,
        this hook falls back to using the x-sdk-user-agent custom header.
        """
        sdk_version = hook_ctx.config.sdk_version
        user_agent = f"youdotcom-python-sdk/{sdk_version}"

        # Try to set the standard User-Agent header first
        request.headers["User-Agent"] = user_agent

        # Check if the header was actually set
        if not request.headers.get("User-Agent"):
            # Fall back to a custom header if the User-Agent couldn't be set
            request.headers["x-sdk-user-agent"] = user_agent

        return request


def init_hooks(hooks: Hooks):
    # pylint: disable=unused-argument
    """Add hooks by calling hooks.register{sdk_init/before_request/after_success/after_error}Hook
    with an instance of a hook that implements that specific Hook interface
    Hooks are registered per SDK instance, and are valid for the lifetime of the SDK instance"""
    hooks.register_before_request_hook(YDCUserAgentOverrideHook())
