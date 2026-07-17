from .types import Hooks, BeforeRequestHook, BeforeRequestContext
import httpx
from typing import Union


# This file is only ever generated once on the first generation and then is free to be modified.
# Any hooks you wish to add should be registered in the init_hooks function. Feel free to define them
# in this file or in separate files in the hooks folder.

_DEFAULT_UA_PREFIX = "speakeasy-sdk/"


class YDCUserAgentOverrideHook(BeforeRequestHook):
    """Hook that overrides the User-Agent header on every request.

    Behaviour:
    - If ``sdk_configuration.user_agent`` has been overridden away from the
      speakeasy-default (``speakeasy-sdk/python ...``), pass it through so
      integrations (langchain-youdotcom, youdotcom-temporal,
      n8n-nodes-youdotcom) can identify their traffic.
    - Otherwise, emit the SDK-default ``youdotcom-python-sdk/{sdk_version}``.
    """

    def before_request(self, hook_ctx: BeforeRequestContext, request: httpx.Request) -> Union[httpx.Request, Exception]:
        sdk_version = hook_ctx.config.sdk_version
        configured_ua = hook_ctx.config.user_agent

        # `not startswith(_DEFAULT_UA_PREFIX)` already handles the default-UA
        # case (the speakeasy default always starts with the prefix), so a
        # separate `configured_ua != __user_agent__` check is redundant.
        is_custom = bool(configured_ua) and not configured_ua.startswith(_DEFAULT_UA_PREFIX)

        request.headers["User-Agent"] = (
            configured_ua if is_custom else f"youdotcom-python-sdk/{sdk_version}"
        )

        return request


def init_hooks(hooks: Hooks):
    # pylint: disable=unused-argument
    """Add hooks by calling hooks.register{sdk_init/before_request/after_success/after_error}Hook
    with an instance of a hook that implements that specific Hook interface
    Hooks are registered per SDK instance, and are valid for the lifetime of the SDK instance"""
    hooks.register_before_request_hook(YDCUserAgentOverrideHook())
