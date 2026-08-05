

from .youerror import YouError
from typing import Any, TYPE_CHECKING

from youdotcom.utils.dynamic_imports import lazy_getattr, lazy_dir

if TYPE_CHECKING:
    from .contentsop import (
        ContentsForbiddenError,
        ContentsForbiddenErrorData,
        ContentsInternalServerError,
        ContentsInternalServerErrorData,
        ContentsUnauthorizedError,
        ContentsUnauthorizedErrorData,
    )
    from .finance_researchop import (
        FinanceResearchForbiddenError,
        FinanceResearchForbiddenErrorData,
        FinanceResearchInternalServerError,
        FinanceResearchInternalServerErrorData,
        FinanceResearchUnauthorizedError,
        FinanceResearchUnauthorizedErrorData,
        FinanceResearchUnprocessableEntityError,
        FinanceResearchUnprocessableEntityErrorData,
    )
    from .forbidden_response_error import (
        ForbiddenResponseError,
        ForbiddenResponseErrorData,
    )
    from .getresearchtaskop import (
        GetResearchTaskForbiddenError,
        GetResearchTaskForbiddenErrorData,
        GetResearchTaskInternalServerError,
        GetResearchTaskInternalServerErrorData,
        GetResearchTaskNotFoundError,
        GetResearchTaskNotFoundErrorData,
        GetResearchTaskUnauthorizedError,
        GetResearchTaskUnauthorizedErrorData,
    )
    from .internalservererror_response import (
        InternalServerErrorResponse,
        InternalServerErrorResponseData,
    )
    from .no_response_error import NoResponseError
    from .paymentrequired_response_error import (
        PaymentRequiredResponseError,
        PaymentRequiredResponseErrorData,
    )
    from .researchop import (
        ResearchForbiddenError,
        ResearchForbiddenErrorData,
        ResearchInternalServerError,
        ResearchInternalServerErrorData,
        ResearchUnauthorizedError,
        ResearchUnauthorizedErrorData,
        ResearchUnprocessableEntityError,
        ResearchUnprocessableEntityErrorData,
    )
    from .responsevalidationerror import ResponseValidationError
    from .streamresearchtaskop import (
        StreamResearchTaskForbiddenError,
        StreamResearchTaskForbiddenErrorData,
        StreamResearchTaskInternalServerError,
        StreamResearchTaskInternalServerErrorData,
        StreamResearchTaskNotFoundError,
        StreamResearchTaskNotFoundErrorData,
        StreamResearchTaskUnauthorizedError,
        StreamResearchTaskUnauthorizedErrorData,
    )
    from .unauthorized_response_error import (
        UnauthorizedResponseError,
        UnauthorizedResponseErrorData,
    )
    from .unprocessableentity_response_error import (
        UnprocessableEntityResponseError,
        UnprocessableEntityResponseErrorData,
    )
    from .youdefaulterror import YouDefaultError

__all__ = [
    "ContentsForbiddenError",
    "ContentsForbiddenErrorData",
    "ContentsInternalServerError",
    "ContentsInternalServerErrorData",
    "ContentsUnauthorizedError",
    "ContentsUnauthorizedErrorData",
    "FinanceResearchForbiddenError",
    "FinanceResearchForbiddenErrorData",
    "FinanceResearchInternalServerError",
    "FinanceResearchInternalServerErrorData",
    "FinanceResearchUnauthorizedError",
    "FinanceResearchUnauthorizedErrorData",
    "FinanceResearchUnprocessableEntityError",
    "FinanceResearchUnprocessableEntityErrorData",
    "ForbiddenResponseError",
    "ForbiddenResponseErrorData",
    "GetResearchTaskForbiddenError",
    "GetResearchTaskForbiddenErrorData",
    "GetResearchTaskInternalServerError",
    "GetResearchTaskInternalServerErrorData",
    "GetResearchTaskNotFoundError",
    "GetResearchTaskNotFoundErrorData",
    "GetResearchTaskUnauthorizedError",
    "GetResearchTaskUnauthorizedErrorData",
    "InternalServerErrorResponse",
    "InternalServerErrorResponseData",
    "NoResponseError",
    "PaymentRequiredResponseError",
    "PaymentRequiredResponseErrorData",
    "ResearchForbiddenError",
    "ResearchForbiddenErrorData",
    "ResearchInternalServerError",
    "ResearchInternalServerErrorData",
    "ResearchUnauthorizedError",
    "ResearchUnauthorizedErrorData",
    "ResearchUnprocessableEntityError",
    "ResearchUnprocessableEntityErrorData",
    "ResponseValidationError",
    "StreamResearchTaskForbiddenError",
    "StreamResearchTaskForbiddenErrorData",
    "StreamResearchTaskInternalServerError",
    "StreamResearchTaskInternalServerErrorData",
    "StreamResearchTaskNotFoundError",
    "StreamResearchTaskNotFoundErrorData",
    "StreamResearchTaskUnauthorizedError",
    "StreamResearchTaskUnauthorizedErrorData",
    "UnauthorizedResponseError",
    "UnauthorizedResponseErrorData",
    "UnprocessableEntityResponseError",
    "UnprocessableEntityResponseErrorData",
    "YouDefaultError",
    "YouError",
]

_dynamic_imports: dict[str, str] = {
    "ContentsForbiddenError": ".contentsop",
    "ContentsForbiddenErrorData": ".contentsop",
    "ContentsInternalServerError": ".contentsop",
    "ContentsInternalServerErrorData": ".contentsop",
    "ContentsUnauthorizedError": ".contentsop",
    "ContentsUnauthorizedErrorData": ".contentsop",
    "FinanceResearchForbiddenError": ".finance_researchop",
    "FinanceResearchForbiddenErrorData": ".finance_researchop",
    "FinanceResearchInternalServerError": ".finance_researchop",
    "FinanceResearchInternalServerErrorData": ".finance_researchop",
    "FinanceResearchUnauthorizedError": ".finance_researchop",
    "FinanceResearchUnauthorizedErrorData": ".finance_researchop",
    "FinanceResearchUnprocessableEntityError": ".finance_researchop",
    "FinanceResearchUnprocessableEntityErrorData": ".finance_researchop",
    "ForbiddenResponseError": ".forbidden_response_error",
    "ForbiddenResponseErrorData": ".forbidden_response_error",
    "GetResearchTaskForbiddenError": ".getresearchtaskop",
    "GetResearchTaskForbiddenErrorData": ".getresearchtaskop",
    "GetResearchTaskInternalServerError": ".getresearchtaskop",
    "GetResearchTaskInternalServerErrorData": ".getresearchtaskop",
    "GetResearchTaskNotFoundError": ".getresearchtaskop",
    "GetResearchTaskNotFoundErrorData": ".getresearchtaskop",
    "GetResearchTaskUnauthorizedError": ".getresearchtaskop",
    "GetResearchTaskUnauthorizedErrorData": ".getresearchtaskop",
    "InternalServerErrorResponse": ".internalservererror_response",
    "InternalServerErrorResponseData": ".internalservererror_response",
    "NoResponseError": ".no_response_error",
    "PaymentRequiredResponseError": ".paymentrequired_response_error",
    "PaymentRequiredResponseErrorData": ".paymentrequired_response_error",
    "ResearchForbiddenError": ".researchop",
    "ResearchForbiddenErrorData": ".researchop",
    "ResearchInternalServerError": ".researchop",
    "ResearchInternalServerErrorData": ".researchop",
    "ResearchUnauthorizedError": ".researchop",
    "ResearchUnauthorizedErrorData": ".researchop",
    "ResearchUnprocessableEntityError": ".researchop",
    "ResearchUnprocessableEntityErrorData": ".researchop",
    "ResponseValidationError": ".responsevalidationerror",
    "StreamResearchTaskForbiddenError": ".streamresearchtaskop",
    "StreamResearchTaskForbiddenErrorData": ".streamresearchtaskop",
    "StreamResearchTaskInternalServerError": ".streamresearchtaskop",
    "StreamResearchTaskInternalServerErrorData": ".streamresearchtaskop",
    "StreamResearchTaskNotFoundError": ".streamresearchtaskop",
    "StreamResearchTaskNotFoundErrorData": ".streamresearchtaskop",
    "StreamResearchTaskUnauthorizedError": ".streamresearchtaskop",
    "StreamResearchTaskUnauthorizedErrorData": ".streamresearchtaskop",
    "UnauthorizedResponseError": ".unauthorized_response_error",
    "UnauthorizedResponseErrorData": ".unauthorized_response_error",
    "UnprocessableEntityResponseError": ".unprocessableentity_response_error",
    "UnprocessableEntityResponseErrorData": ".unprocessableentity_response_error",
    "YouDefaultError": ".youdefaulterror",
}


def __getattr__(attr_name: str) -> Any:
    return lazy_getattr(
        attr_name, package=__package__, dynamic_imports=_dynamic_imports
    )


def __dir__():
    return lazy_dir(dynamic_imports=_dynamic_imports)
