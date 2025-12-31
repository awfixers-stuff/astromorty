"""Discord signature verification for HTTP endpoints.

This module provides security functions for verifying Discord HTTP requests,
including signature validation using Ed25519 cryptography.
"""

from fastapi import Header, HTTPException, Request

from astromorty.shared.config import CONFIG
from loguru import logger


def verify_signature(
    request_body: bytes,
    signature: str,
    timestamp: str,
) -> bool:
    """
    Verify Discord request signature using Ed25519.

    Discord signs all HTTP requests with an Ed25519 signature. This function
    verifies that the request body and timestamp match the signature using
    the bot's public key.

    Parameters
    ----------
    request_body : bytes
        Raw request body bytes
    signature : str
        X-Signature-Ed25519 header value (hex-encoded)
    timestamp : str
        X-Signature-Timestamp header value

    Returns
    -------
    bool
        True if signature is valid, False otherwise
    """
    try:
        import nacl.exceptions
        import nacl.signing

        # Get public key from config
        public_key_hex = CONFIG.DISCORD_PUBLIC_KEY
        if not public_key_hex:
            logger.error("DISCORD_PUBLIC_KEY not configured")
            return False

        # Create verify key from hex-encoded public key
        public_key = nacl.signing.VerifyKey(
            bytes.fromhex(public_key_hex),
        )

        # Construct message: timestamp + request body (as string)
        message = f"{timestamp}{request_body.decode()}".encode()

        # Verify signature
        try:
            public_key.verify(message, bytes.fromhex(signature))
            return True
        except nacl.exceptions.BadSignatureError:
            logger.warning("Invalid Discord signature")
            return False

    except Exception as e:
        logger.error(f"Error verifying signature: {e}")
        return False


async def verify_discord_request(request: Request) -> None:
    """
    Middleware function to verify Discord request signatures.

    Extracts signature headers from the request and verifies them against
    the request body. Raises HTTPException if verification fails.

    Parameters
    ----------
    request : Request
        FastAPI request object

    Raises
    ------
    HTTPException
        If signature headers are missing or verification fails
    """
    # Extract signature headers
    signature = request.headers.get("X-Signature-Ed25519")
    timestamp = request.headers.get("X-Signature-Timestamp")

    if not signature or not timestamp:
        logger.warning("Missing Discord signature headers")
        raise HTTPException(
            status_code=401,
            detail="Missing signature headers (X-Signature-Ed25519, X-Signature-Timestamp)",
        )

    # Read request body
    body = await request.body()

    # Verify signature
    if not verify_signature(body, signature, timestamp):
        logger.warning("Discord signature verification failed")
        raise HTTPException(
            status_code=401,
            detail="Invalid signature",
        )

