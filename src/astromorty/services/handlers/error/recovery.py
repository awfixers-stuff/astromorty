"""Error recovery mechanisms for transient failures."""

import asyncio
from typing import Any, Callable, TypeVar

import discord
import httpx
from discord.ext import commands
from loguru import logger

T = TypeVar("T")

# Retry configuration
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0  # seconds
MAX_BACKOFF = 10.0  # seconds
BACKOFF_MULTIPLIER = 2.0

# Transient error types that should be retried
TRANSIENT_ERRORS = (
    discord.RateLimited,
    httpx.TimeoutException,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
    httpx.ConnectError,
    httpx.NetworkError,
)


async def retry_with_backoff(
    func: Callable[..., Any],
    *args: Any,
    max_retries: int = MAX_RETRIES,
    initial_backoff: float = INITIAL_BACKOFF,
    max_backoff: float = MAX_BACKOFF,
    backoff_multiplier: float = BACKOFF_MULTIPLIER,
    **kwargs: Any,
) -> Any:
    """Retry a function with exponential backoff on transient errors.

    Parameters
    ----------
    func : Callable
        The async function to retry.
    *args : Any
        Positional arguments to pass to the function.
    max_retries : int
        Maximum number of retry attempts.
    initial_backoff : float
        Initial backoff delay in seconds.
    max_backoff : float
        Maximum backoff delay in seconds.
    backoff_multiplier : float
        Multiplier for exponential backoff.
    **kwargs : Any
        Keyword arguments to pass to the function.

    Returns
    -------
    Any
        The result of the function call.

    Raises
    ------
    Exception
        The last exception if all retries are exhausted.
    """
    last_exception: Exception | None = None
    backoff = initial_backoff

    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except TRANSIENT_ERRORS as e:
            last_exception = e

            if attempt < max_retries:
                # Calculate backoff with jitter
                wait_time = min(backoff, max_backoff)
                logger.debug(
                    f"Transient error {type(e).__name__} on attempt {attempt + 1}/{max_retries + 1}, "
                    f"retrying in {wait_time:.2f}s"
                )
                await asyncio.sleep(wait_time)
                backoff *= backoff_multiplier
            else:
                logger.warning(
                    f"All {max_retries + 1} retry attempts exhausted for {func.__name__}"
                )
        except Exception as e:
            # Non-transient error, don't retry
            logger.debug(f"Non-transient error {type(e).__name__}, not retrying")
            raise

    # If we get here, all retries were exhausted
    if last_exception:
        raise last_exception

    raise RuntimeError("Retry logic reached unexpected state")


def is_transient_error(error: Exception) -> bool:
    """Check if an error is transient and should be retried.

    Parameters
    ----------
    error : Exception
        The error to check.

    Returns
    -------
    bool
        True if the error is transient and should be retried.
    """
    return isinstance(error, TRANSIENT_ERRORS)


async def handle_rate_limit(
    error: discord.RateLimited,
    retry_after: float | None = None,
) -> None:
    """Handle Discord rate limit errors with appropriate backoff.

    Parameters
    ----------
    error : discord.RateLimited
        The rate limit error.
    retry_after : float, optional
        Override retry_after from error if provided.
    """
    wait_time = retry_after if retry_after is not None else error.retry_after
    logger.info(f"Rate limited, waiting {wait_time:.2f}s before retry")
    await asyncio.sleep(wait_time)


async def handle_network_error(
    error: httpx.HTTPError,
    retry_count: int = 0,
) -> bool:
    """Handle network errors and determine if retry is appropriate.

    Parameters
    ----------
    error : httpx.HTTPError
        The network error.
    retry_count : int
        Current retry attempt number.

    Returns
    -------
    bool
        True if retry is recommended, False otherwise.
    """
    if isinstance(error, (httpx.TimeoutException, httpx.ConnectError)):
        if retry_count < MAX_RETRIES:
            logger.debug(f"Network error {type(error).__name__}, will retry")
            return True

    logger.warning(f"Network error {type(error).__name__}, not retrying")
    return False


