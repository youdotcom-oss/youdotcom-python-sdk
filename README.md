<div align="center">
  <img width="600" height="315" alt="image" src="https://github.com/user-attachments/assets/149ddec2-8bd7-49f3-93fa-833714ad201f" />
</div>
<div align="center">
The official developer-friendly & type-safe Python SDK specifically designed to leverage the You.com API.
</div>
<br >
<div align="center">
    <a href="https://www.speakeasy.com/?utm_source=openapi&utm_campaign=python"><img src="https://www.speakeasy.com/assets/badges/built-by-speakeasy.svg" /></a>
    <a href="https://opensource.org/licenses/MIT">
        <img src="https://img.shields.io/badge/License-MIT-blue.svg" style="width: 100px; height: 28px;" />
    </a>
</div>

<!-- Start Table of Contents [toc] -->
## Table of Contents
<!-- $toc-max-depth=2 -->
  * [SDK Installation](#sdk-installation)
  * [IDE Support](#ide-support)
  * [SDK Example Usage](#sdk-example-usage)
  * [Authentication](#authentication)
  * [Available Resources and Operations](#available-resources-and-operations)
  * [Server-sent event streaming](#server-sent-event-streaming)
  * [Retries](#retries)
  * [Error Handling](#error-handling)
  * [Server Selection](#server-selection)
  * [Custom HTTP Client](#custom-http-client)
  * [Resource Management](#resource-management)
  * [Debugging](#debugging)
* [Development](#development)
  * [Maturity](#maturity)
  * [Contributions](#contributions)

<!-- End Table of Contents [toc] -->

<!-- Start SDK Installation [installation] -->
## SDK Installation

> [!NOTE]
> **Python version upgrade policy**
>
> Once a Python version reaches its [official end of life date](https://devguide.python.org/versions/), a 3-month grace period is provided for users to upgrade. Following this grace period, the minimum python version supported in the SDK will be updated.

The SDK can be installed with *uv*, *pip*, or *poetry* package managers.

### uv

*uv* is a fast Python package installer and resolver, designed as a drop-in replacement for pip and pip-tools. It's recommended for its speed and modern Python tooling capabilities.

```bash
uv add youdotcom
```

### PIP

*PIP* is the default package installer for Python, enabling easy installation and management of packages from PyPI via the command line.

```bash
pip install youdotcom
```

### Poetry

*Poetry* is a modern tool that simplifies dependency management and package publishing by using a single `pyproject.toml` file to handle project metadata and dependencies.

```bash
poetry add youdotcom
```

### Shell and script usage with `uv`

You can use this SDK in a Python shell with [uv](https://docs.astral.sh/uv/) and the `uvx` command that comes with it like so:

```shell
uvx --from youdotcom python
```

It's also possible to write a standalone Python script without needing to set up a whole project like so:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "youdotcom",
# ]
# ///

from youdotcom import You

sdk = You(
  # SDK arguments
)

# Rest of script here...
```

Once that is saved to a file, you can run it with `uv run script.py` where
`script.py` can be replaced with the actual file name.
<!-- End SDK Installation [installation] -->

<!-- Start IDE Support [idesupport] -->
## IDE Support

### PyCharm

Generally, the SDK will work well with most IDEs out of the box. However, when using PyCharm, you can enjoy much better integration with Pydantic by installing an additional plugin.

- [PyCharm Pydantic Plugin](https://docs.pydantic.dev/latest/integrations/pycharm/)
<!-- End IDE Support [idesupport] -->

<!-- Start SDK Example Usage [usage] -->
## SDK Example Usage

> Tip: Additional examples can be found in the [examples](examples/) folder


### Example with Express agent

```python
# Synchronous Example with Express agent
from youdotcom import You
from youdotcom.types.typesafe_models import (
    AgentType,
    stream_text_tokens
)

with You(
    api_key_auth="Your You.com API Key",
) as you:
    res = you.agents.runs.create(
        agent=AgentType.EXPRESS,
        input="Teach me how to make an omelet",
        stream=True,
    )
    stream_text_tokens(res)

```

The same SDK client can also be used to make asynchronous requests by importing asyncio.

```python
# Asynchronous Example
import asyncio
from youdotcom import You
from youdotcom.types.typesafe_models import AgentType

async def main():
    async with You(
        api_key_auth="Your You.com API Key",
    ) as you:
        res = await you.agents.runs.create_async(
            agent=AgentType.EXPRESS,
            input="What is a Rain Frog?",
            stream=False,
        )

        async for event in res:
            # handle event
            print(event, flush=True)

asyncio.run(main())

```

### Example with Advanced agent and tools

```python
# Synchronous Example with Express agent
from youdotcom import You
from youdotcom.models import ComputeTool, ResearchTool
from youdotcom.types.typesafe_models import (
    AgentType,
    SearchEffort,
    Verbosity,
    get_text_tokens,
)

with You(
    api_key_auth="Your You.com API Key",
) as you:
    res = you.agents.runs.create(
            agent=AgentType.ADVANCED,
            input="Research and calculate the latest trends and the square root of 169. Show your work.",
            stream=False,
            tools=[
                ComputeTool(),
                ResearchTool(
                    search_effort=SearchEffort.AUTO,
                    report_verbosity=Verbosity.HIGH,
                ),
            ]
    ) 
    get_text_tokens(res)

```

### Example with Contents

```python
# Synchronous Example with the Contents API
from youdotcom import You
from youdotcom.types.typesafe_models import (
    Format,
    print_contents
)

with You(
    api_key_auth="Your You.com API Key",
) as you:
    res = you.contents.generate(
        urls=[
            "https://www.python.org",
            "https://www.example.com",
        ],
        format_=Format.HTML,
    )
    print_contents(res)

```

### Example with Search V1

```python
# Synchronous Example with the Search V1 API
from youdotcom import You
from youdotcom.types.typesafe_models import print_search

with You(
    api_key_auth="Your You.com API Key",
) as you:
    res = you.search.unified(
        query="latest AI developments",
    )
    print_search(res)
```


<!-- End SDK Example Usage [usage] -->

<!-- Start Authentication [security] -->
## Authentication

### Per-Client Security Schemes

This SDK supports the following security scheme globally:

| Name           | Type   | Scheme  | Environment Variable |
| -------------- | ------ | ------- | -------------------- |
| `api_key_auth` | apiKey | API key | `YOU_API_KEY_AUTH`   |

To authenticate with the API the `api_key_auth` parameter must be set when initializing the SDK client instance. It's best practice to use an environment variable to access this key.
```python
import os
from youdotcom import You


with You(
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
) as you:
    # Rest of application code ...
```

<!-- End Authentication [security] -->

<!-- Start Available Resources and Operations [operations] -->
## Available Resources and Operations

<details open>
<summary>Available methods</summary>

#### [agents.runs](docs/sdks/runs/README.md)

* [create](docs/sdks/runs/README.md#create)

### [contents](docs/sdks/contents/README.md)

* [generate](docs/sdks/contents/README.md#generate) - Returns the content of the web pages

### [search](docs/sdks/search/README.md)

* [unified](docs/sdks/search/README.md#unified) - Returns a list of unified search results from web and news sources

</details>
<!-- End Available Resources and Operations [operations] -->

<!-- Start Server-sent event streaming [eventstream] -->
## Server-sent event streaming

[Server-sent events][mdn-sse] are used to stream content from certain
operations. These operations will expose the stream as [Generator][generator] that
can be consumed using a simple `for` loop. The loop will
terminate when the server no longer has any events to send and closes the
underlying connection.  

The stream is also a [Context Manager][context-manager] and can be used with the `with` statement and will close the
underlying connection when the context is exited.

For simple text output when streaming, you can use the stream_text_tokens helper utility (see Example section).

```python
from youdotcom import You, AgentType

with You(
    api_key_auth="Your You.com API Key",
) as you:
    res = you.agents.runs.create(
        agent=AgentType.EXPRESS,
        input="Teach me how to make an omelet",
        stream=True,
    )
    with res as event_stream:
        for event in event_stream:
            if event.response:
                response = event.response
                    if response.delta:
                        print(response.delta, end="", flush=True)

```

[mdn-sse]: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events
[generator]: https://book.pythontips.com/en/latest/generators.html
[context-manager]: https://book.pythontips.com/en/latest/context_managers.html
<!-- End Server-sent event streaming [eventstream] -->

<!-- Start Retries [retries] -->
## Retries

Some of the endpoints in this SDK support retries. If you use the SDK without any configuration, it will fall back to the default retry strategy provided by the API. However, the default retry strategy can be overridden on a per-operation basis, or across the entire SDK.

To change the default retry strategy for a single API call, simply provide a `RetryConfig` object to the call:
```python
import os
from youdotcom import You
from youdotcom.utils import BackoffStrategy, RetryConfig


with You(
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
) as you:

    res = you.agents.runs.create(agent="express", input="What is the capital of France?", stream=False, tools=[
        {
            "type": "compute",
        },
    ],
        RetryConfig("backoff", BackoffStrategy(1, 50, 1.1, 100), False))

    with res as event_stream:
        for event in event_stream:
            # handle event
            print(event, flush=True)

```

If you'd like to override the default retry strategy for all operations that support retries, you can use the `retry_config` optional parameter when initializing the SDK:
```python
import os
from youdotcom import You
from youdotcom.utils import BackoffStrategy, RetryConfig


with You(
    retry_config=RetryConfig("backoff", BackoffStrategy(1, 50, 1.1, 100), False),
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
) as you:

    res = you.agents.runs.create(agent="express", input="What is the capital of France?", stream=False, tools=[
        {
            "type": "compute",
        },
    ])

    with res as event_stream:
        for event in event_stream:
            # handle event
            print(event, flush=True)

```
<!-- End Retries [retries] -->

<!-- Start Error Handling [errors] -->
## Error Handling

[`YouError`](./src/youdotcom/errors/youerror.py) is the base class for all HTTP error responses. It has the following properties:

| Property           | Type             | Description                                                                             |
| ------------------ | ---------------- | --------------------------------------------------------------------------------------- |
| `err.message`      | `str`            | Error message                                                                           |
| `err.status_code`  | `int`            | HTTP response status code eg `404`                                                      |
| `err.headers`      | `httpx.Headers`  | HTTP response headers                                                                   |
| `err.body`         | `str`            | HTTP body. Can be empty string if no body is returned.                                  |
| `err.raw_response` | `httpx.Response` | Raw HTTP response                                                                       |
| `err.data`         |                  | Optional. Some errors may contain structured data. [See Error Classes](#error-classes). |

### Example
```python
import os
from youdotcom import You, errors


with You(
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
) as you:
    res = None
    try:

        res = you.agents.runs.create(agent="express", input="What is the capital of France?", stream=False, tools=[
            {
                "type": "compute",
            },
        ])

        with res as event_stream:
            for event in event_stream:
                # handle event
                print(event, flush=True)


    except errors.YouError as e:
        # The base class for HTTP error responses
        print(e.message)
        print(e.status_code)
        print(e.body)
        print(e.headers)
        print(e.raw_response)

        # Depending on the method different errors may be thrown
        if isinstance(e, errors.BadRequestError):
            print(e.data.errors)  # List[models.BadRequestError]
```

### Error Classes
**Primary error:**
* [`YouError`](./src/youdotcom/errors/youerror.py): The base class for HTTP error responses.

<details><summary>Less common errors (14)</summary>

<br />

**Network errors:**
* [`httpx.RequestError`](https://www.python-httpx.org/exceptions/#httpx.RequestError): Base class for request errors.
    * [`httpx.ConnectError`](https://www.python-httpx.org/exceptions/#httpx.ConnectError): HTTP client was unable to make a request to a server.
    * [`httpx.TimeoutException`](https://www.python-httpx.org/exceptions/#httpx.TimeoutException): HTTP request timed out.


**Inherit from [`YouError`](./src/youdotcom/errors/youerror.py)**:
* [`BadRequestError`](./src/youdotcom/errors/badrequesterror.py): Bad Request. Invalid or malformed request body/parameters. Status code `400`. Applicable to 1 of 3 methods.*
* [`PostV1ContentsUnauthorizedError`](./src/youdotcom/errors/postv1contentsunauthorizederror.py): Unauthorized. Status code `401`. Applicable to 1 of 3 methods.*
* [`GetV1SearchUnauthorizedError`](./src/youdotcom/errors/getv1searchunauthorizederror.py): Unauthorized. Problems with API key. Status code `401`. Applicable to 1 of 3 methods.*
* [`PostV1AgentsRunsUnauthorizedError`](./src/youdotcom/errors/postv1agentsrunsunauthorizederror.py): Unauthorized. Problems with API key. Status code `401`. Applicable to 1 of 3 methods.*
* [`PostV1ContentsForbiddenError`](./src/youdotcom/errors/postv1contentsforbiddenerror.py): Forbidden. Status code `403`. Applicable to 1 of 3 methods.*
* [`GetV1SearchForbiddenError`](./src/youdotcom/errors/getv1searchforbiddenerror.py): Forbidden. API key lacks scope for this path. Status code `403`. Applicable to 1 of 3 methods.*
* [`PostV1AgentsRunsForbiddenError`](./src/youdotcom/errors/postv1agentsrunsforbiddenerror.py): Forbidden. API key lacks scope for this path. Status code `403`. Applicable to 1 of 3 methods.*
* [`PostV1ContentsInternalServerError`](./src/youdotcom/errors/postv1contentsinternalservererror.py): Internal Server Error. Status code `500`. Applicable to 1 of 3 methods.*
* [`GetV1SearchInternalServerError`](./src/youdotcom/errors/getv1searchinternalservererror.py): Internal Server Error during authentication/authorization middleware. Status code `500`. Applicable to 1 of 3 methods.*
* [`ResponseValidationError`](./src/youdotcom/errors/responsevalidationerror.py): Type mismatch between the response data and the expected Pydantic model. Provides access to the Pydantic validation error via the `cause` attribute.

</details>

\* Check [the method documentation](#available-resources-and-operations) to see if the error is applicable.
<!-- End Error Handling [errors] -->

<!-- Start Server Selection [server] -->
## Server Selection

### Select Server by Index

You can override the default server globally by passing a server index to the `server_idx: int` optional parameter when initializing the SDK client instance. The selected server will then be used as the default on the operations that use it. This table lists the indexes associated with the available servers:

| #   | Server                 | Description                          |
| --- | ---------------------- | ------------------------------------ |
| 0   | `https://ydc-index.io` | Production - Search and Contents API |
| 1   | `https://api.you.com`  | Production - Agents API              |

#### Example

```python
import os
from youdotcom import You


with You(
    server_idx=0,
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
) as you:

    res = you.agents.runs.create(agent="express", input="What is the capital of France?", stream=False, tools=[
        {
            "type": "compute",
        },
    ])

    with res as event_stream:
        for event in event_stream:
            # handle event
            print(event, flush=True)

```

### Override Server URL Per-Client

The default server can also be overridden globally by passing a URL to the `server_url: str` optional parameter when initializing the SDK client instance. For example:
```python
import os
from youdotcom import You


with You(
    server_url="https://api.you.com",
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
) as you:

    res = you.agents.runs.create(agent="express", input="What is the capital of France?", stream=False, tools=[
        {
            "type": "compute",
        },
    ])

    with res as event_stream:
        for event in event_stream:
            # handle event
            print(event, flush=True)

```

### Override Server URL Per-Operation

The server URL can also be overridden on a per-operation basis, provided a server list was specified for the operation. For example:
```python
import os
from youdotcom import You


with You(
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
) as you:

    res = you.agents.runs.create(agent="express", input="What is the capital of France?", stream=False, tools=[
        {
            "type": "compute",
        },
    ], server_url="https://api.you.com")

    with res as event_stream:
        for event in event_stream:
            # handle event
            print(event, flush=True)

```
<!-- End Server Selection [server] -->

<!-- Start Custom HTTP Client [http-client] -->
## Custom HTTP Client

The Python SDK makes API calls using the [httpx](https://www.python-httpx.org/) HTTP library.  In order to provide a convenient way to configure timeouts, cookies, proxies, custom headers, and other low-level configuration, you can initialize the SDK client with your own HTTP client instance.
Depending on whether you are using the sync or async version of the SDK, you can pass an instance of `HttpClient` or `AsyncHttpClient` respectively, which are Protocol's ensuring that the client has the necessary methods to make API calls.
This allows you to wrap the client with your own custom logic, such as adding custom headers, logging, or error handling, or you can just pass an instance of `httpx.Client` or `httpx.AsyncClient` directly.

For example, you could specify a header for every request that this sdk makes as follows:
```python
from youdotcom import You
import httpx

http_client = httpx.Client(headers={"x-custom-header": "someValue"})
s = You(client=http_client)
```

or you could wrap the client with your own custom logic:
```python
from youdotcom import You
from youdotcom.httpclient import AsyncHttpClient
import httpx

class CustomClient(AsyncHttpClient):
    client: AsyncHttpClient

    def __init__(self, client: AsyncHttpClient):
        self.client = client

    async def send(
        self,
        request: httpx.Request,
        *,
        stream: bool = False,
        auth: Union[
            httpx._types.AuthTypes, httpx._client.UseClientDefault, None
        ] = httpx.USE_CLIENT_DEFAULT,
        follow_redirects: Union[
            bool, httpx._client.UseClientDefault
        ] = httpx.USE_CLIENT_DEFAULT,
    ) -> httpx.Response:
        request.headers["Client-Level-Header"] = "added by client"

        return await self.client.send(
            request, stream=stream, auth=auth, follow_redirects=follow_redirects
        )

    def build_request(
        self,
        method: str,
        url: httpx._types.URLTypes,
        *,
        content: Optional[httpx._types.RequestContent] = None,
        data: Optional[httpx._types.RequestData] = None,
        files: Optional[httpx._types.RequestFiles] = None,
        json: Optional[Any] = None,
        params: Optional[httpx._types.QueryParamTypes] = None,
        headers: Optional[httpx._types.HeaderTypes] = None,
        cookies: Optional[httpx._types.CookieTypes] = None,
        timeout: Union[
            httpx._types.TimeoutTypes, httpx._client.UseClientDefault
        ] = httpx.USE_CLIENT_DEFAULT,
        extensions: Optional[httpx._types.RequestExtensions] = None,
    ) -> httpx.Request:
        return self.client.build_request(
            method,
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            timeout=timeout,
            extensions=extensions,
        )

s = You(async_client=CustomClient(httpx.AsyncClient()))
```
<!-- End Custom HTTP Client [http-client] -->

<!-- Start Resource Management [resource-management] -->
## Resource Management

The `You` class implements the context manager protocol and registers a finalizer function to close the underlying sync and async HTTPX clients it uses under the hood. This will close HTTP connections, release memory and free up other resources held by the SDK. In short-lived Python programs and notebooks that make a few SDK method calls, resource management may not be a concern. However, in longer-lived programs, it is beneficial to create a single SDK instance via a [context manager][context-manager] and reuse it across the application.

[context-manager]: https://docs.python.org/3/reference/datamodel.html#context-managers

```python
import os
from youdotcom import You
def main():

    with You(
        api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
    ) as you:
        # Rest of application here...


# Or when using async:
async def amain():

    async with You(
        api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
    ) as you:
        # Rest of application here...
```
<!-- End Resource Management [resource-management] -->

<!-- Start Debugging [debug] -->
## Debugging

You can setup your SDK to emit debug logs for SDK requests and responses.

You can pass your own logger class directly into your SDK.
```python
from youdotcom import You
import logging

logging.basicConfig(level=logging.DEBUG)
s = You(debug_logger=logging.getLogger("youdotcom"))
```

You can also enable a default debug logger by setting an environment variable `YOU_DEBUG` to true.
<!-- End Debugging [debug] -->

<!-- Placeholder for Future Speakeasy SDK Sections -->

# Development

## Maturity

This SDK is in beta, and there may be breaking changes between versions without a major version update. Therefore, we recommend pinning usage
to a specific package version. This way, you can install the same version each time without breaking changes unless you are intentionally
looking for the latest version.

## Contributions

While we value open-source contributions to this SDK, this library is generated programmatically. Any manual changes added to internal files will be overwritten on the next generation. 
We look forward to hearing your feedback. Feel free to open a PR or an issue with a proof of concept and we'll do our best to include it in a future release. 

### SDK Created by [Speakeasy](https://www.speakeasy.com/?utm_source=youdotcom&utm_campaign=python)
