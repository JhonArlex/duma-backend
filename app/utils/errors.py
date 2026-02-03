"""
Error handling utilities for standardized API error responses.

This module provides:
- Error code constants for consistent error identification
- Standardized error response formatting for i18n support
- Default English messages for all error codes
"""

from typing import Optional, Dict, Any
from flask import jsonify


class ErrorCode:
    """Error code constants for API responses."""
    
    # Validation Errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    
    # Authentication Errors
    EMAIL_ALREADY_EXISTS = "EMAIL_ALREADY_EXISTS"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    OAUTH_EMAIL_REQUIRED = "OAUTH_EMAIL_REQUIRED"
    EMAIL_EXISTS_WITH_DIFFERENT_PROVIDER = "EMAIL_EXISTS_WITH_DIFFERENT_PROVIDER"
    USER_INACTIVE = "USER_INACTIVE"
    
    # User/Resource Not Found
    USER_NOT_FOUND = "USER_NOT_FOUND"
    ADDRESS_NOT_FOUND = "ADDRESS_NOT_FOUND"
    ORDER_NOT_FOUND = "ORDER_NOT_FOUND"
    PAYMENT_NOT_FOUND = "PAYMENT_NOT_FOUND"
    CART_NOT_FOUND = "CART_NOT_FOUND"
    CART_ITEM_NOT_FOUND = "CART_ITEM_NOT_FOUND"
    ROLE_NOT_FOUND = "ROLE_NOT_FOUND"
    PERMISSION_NOT_FOUND = "PERMISSION_NOT_FOUND"
    STORE_NOT_FOUND = "STORE_NOT_FOUND"
    
    # Business Logic Errors
    OAUTH_PASSWORD_CHANGE_NOT_ALLOWED = "OAUTH_PASSWORD_CHANGE_NOT_ALLOWED"
    INVALID_PASSWORD = "INVALID_PASSWORD"
    SELF_DELETE_NOT_ALLOWED = "SELF_DELETE_NOT_ALLOWED"
    INVALID_ADDRESS = "INVALID_ADDRESS"
    INVALID_STATUS_TRANSITION = "INVALID_STATUS_TRANSITION"
    ORDER_CANNOT_BE_CANCELLED = "ORDER_CANNOT_BE_CANCELLED"
    ORDER_ALREADY_PAID = "ORDER_ALREADY_PAID"
    
    # Missing Required Data
    MISSING_USER_ID = "MISSING_USER_ID"
    MISSING_EMAIL = "MISSING_EMAIL"
    
    # External Service Errors
    STRIPE_ERROR = "STRIPE_ERROR"
    WEBHOOK_SIGNATURE_INVALID = "WEBHOOK_SIGNATURE_INVALID"
    
    # Permission Errors
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"


# Default error messages in English (for fallback)
DEFAULT_ERROR_MESSAGES = {
    ErrorCode.VALIDATION_ERROR: "Validation failed",
    ErrorCode.EMAIL_ALREADY_EXISTS: "Email already registered",
    ErrorCode.INVALID_CREDENTIALS: "Invalid email or password",
    ErrorCode.OAUTH_EMAIL_REQUIRED: "Email is required for OAuth login",
    ErrorCode.EMAIL_EXISTS_WITH_DIFFERENT_PROVIDER: "Email already registered with a different provider",
    ErrorCode.USER_INACTIVE: "User account is inactive",
    ErrorCode.USER_NOT_FOUND: "User not found",
    ErrorCode.ADDRESS_NOT_FOUND: "Address not found",
    ErrorCode.ORDER_NOT_FOUND: "Order not found",
    ErrorCode.PAYMENT_NOT_FOUND: "Payment not found",
    ErrorCode.CART_NOT_FOUND: "Cart not found",
    ErrorCode.CART_ITEM_NOT_FOUND: "Cart item not found",
    ErrorCode.ROLE_NOT_FOUND: "Role not found",
    ErrorCode.PERMISSION_NOT_FOUND: "Permission not found",
    ErrorCode.STORE_NOT_FOUND: "Store not found",
    ErrorCode.OAUTH_PASSWORD_CHANGE_NOT_ALLOWED: "Cannot change password for OAuth users",
    ErrorCode.INVALID_PASSWORD: "Current password is incorrect",
    ErrorCode.SELF_DELETE_NOT_ALLOWED: "Cannot delete your own account",
    ErrorCode.INVALID_ADDRESS: "Invalid or inaccessible address",
    ErrorCode.INVALID_STATUS_TRANSITION: "Invalid status transition",
    ErrorCode.ORDER_CANNOT_BE_CANCELLED: "Order cannot be cancelled in its current status",
    ErrorCode.ORDER_ALREADY_PAID: "Order has already been paid",
    ErrorCode.MISSING_USER_ID: "User ID is required",
    ErrorCode.MISSING_EMAIL: "Email is required",
    ErrorCode.STRIPE_ERROR: "Payment processing error",
    ErrorCode.WEBHOOK_SIGNATURE_INVALID: "Invalid webhook signature",
    ErrorCode.PERMISSION_DENIED: "Permission denied",
    ErrorCode.INSUFFICIENT_PERMISSIONS: "Insufficient permissions to perform this action",
}


def error_response(
    code: str,
    message: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        code: Error code constant (use ErrorCode class)
        message: Custom error message (optional, uses default if not provided)
        details: Additional error details (e.g., validation errors)
    
    Returns:
        Dictionary with standardized error structure
        
    Example:
        >>> error_response(ErrorCode.EMAIL_ALREADY_EXISTS)
        {'error': {'code': 'EMAIL_ALREADY_EXISTS', 'message': 'Email already registered', 'details': None}}
        
        >>> error_response(ErrorCode.VALIDATION_ERROR, details={'email': ['Email is required']})
        {'error': {'code': 'VALIDATION_ERROR', 'message': 'Validation failed', 'details': {'email': [...]}}}
    """
    if message is None:
        message = DEFAULT_ERROR_MESSAGES.get(code, "An error occurred")
    
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details
        }
    }


def validation_error_response(validation_errors: Dict[str, list]) -> Dict[str, Any]:
    """
    Create a standardized validation error response from marshmallow ValidationError.
    
    Args:
        validation_errors: Dictionary of field names to error messages
        
    Returns:
        Dictionary with standardized error structure
        
    Example:
        >>> validation_error_response({'email': ['Email is required'], 'password': ['Too short']})
        {'error': {'code': 'VALIDATION_ERROR', 'message': 'Validation failed', 'details': {...}}}
    """
    return error_response(
        ErrorCode.VALIDATION_ERROR,
        details=validation_errors
    )
