from .types import Hooks


def init_hooks(hooks: Hooks):
    """Register SDK hooks.

    The user-agent is set directly from ``sdk_configuration.user_agent`` in
    ``BaseSDK._build_request`` — no hook needed. Integrations that want a
    custom UA simply override ``client.sdk_configuration.user_agent``.
    """
    pass
