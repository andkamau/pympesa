"""Main M-PESA API client."""

from __future__ import annotations

from typing import Any

import requests

from .auth import TokenManager
from .endpoints import Environment, get_url
from .exceptions import APIError, ValidationError
from .utils import format_phone_number, generate_password, generate_timestamp


class Pympesa:
    """M-PESA Daraja API client.

    Provides methods for all M-PESA API operations including STK Push,
    C2B, B2C, B2B, reversals, and more.

    Example:
        >>> from pympesa import Pympesa
        >>> client = Pympesa(
        ...     consumer_key="your_key",
        ...     consumer_secret="your_secret",
        ...     env="sandbox"
        ... )
        >>> response = client.stk_push(
        ...     shortcode="174379",
        ...     passkey="your_passkey",
        ...     amount=100,
        ...     phone="254712345678",
        ...     callback_url="https://example.com/callback",
        ...     account_reference="Order123",
        ...     description="Payment for order"
        ... )
    """

    def __init__(
        self,
        consumer_key: str,
        consumer_secret: str,
        env: Environment | str = Environment.SANDBOX,
        timeout: int = 30,
    ) -> None:
        """Initialize the M-PESA client.

        Args:
            consumer_key: M-PESA API consumer key.
            consumer_secret: M-PESA API consumer secret.
            env: API environment ("sandbox" or "production").
            timeout: Request timeout in seconds.
        """
        self.env = Environment(env) if isinstance(env, str) else env
        self.timeout = timeout
        self._token_manager = TokenManager(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            env=self.env,
            timeout=timeout,
        )

    def _get_headers(self) -> dict[str, str]:
        """Get headers with current access token."""
        token = self._token_manager.get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _request(
        self,
        endpoint: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Make an API request.

        Args:
            endpoint: The endpoint key.
            payload: The request payload.

        Returns:
            The JSON response data.

        Raises:
            APIError: If the request fails.
        """
        url = get_url(endpoint, self.env)
        headers = self._get_headers()

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise APIError(f"Request failed: {e}") from e

        data = self._safe_json(response)

        # Check for error responses
        if response.status_code >= 400:
            error_message = data.get("errorMessage") or data.get("message") or response.text
            raise APIError(
                message=f"API error: {error_message}",
                status_code=response.status_code,
                response_data=data,
                request_id=data.get("requestId"),
            )

        return data

    def _safe_json(self, response: requests.Response) -> dict[str, Any]:
        """Safely extract JSON from response."""
        try:
            return response.json()
        except ValueError:
            return {}

    # =========================================================================
    # M-PESA Express (STK Push)
    # =========================================================================

    def stk_push(
        self,
        shortcode: str,
        passkey: str,
        amount: int,
        phone: str,
        callback_url: str,
        account_reference: str,
        description: str,
        transaction_type: str = "CustomerPayBillOnline",
    ) -> dict[str, Any]:
        """Initiate an STK Push (M-PESA Express) request.

        Triggers a payment prompt on the customer's phone.

        Args:
            shortcode: Business shortcode (Paybill or Till number).
            passkey: Lipa Na M-PESA passkey from Safaricom.
            amount: Amount to charge (integer, no decimals).
            phone: Customer's phone number (will be formatted to 254XXXXXXXXX).
            callback_url: HTTPS URL for payment notification.
            account_reference: Your reference for the transaction.
            description: Transaction description.
            transaction_type: "CustomerPayBillOnline" or "CustomerBuyGoodsOnline".

        Returns:
            API response with CheckoutRequestID and other details.

        Raises:
            ValidationError: If parameters are invalid.
            APIError: If the API request fails.
        """
        if amount <= 0:
            raise ValidationError("Amount must be greater than 0", field="amount")

        phone_formatted = format_phone_number(phone)
        timestamp = generate_timestamp()
        password = generate_password(shortcode, passkey, timestamp)

        payload = {
            "BusinessShortCode": shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": transaction_type,
            "Amount": amount,
            "PartyA": phone_formatted,
            "PartyB": shortcode,
            "PhoneNumber": phone_formatted,
            "CallBackURL": callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": description,
        }

        return self._request("stk_push", payload)

    def stk_query(
        self,
        shortcode: str,
        passkey: str,
        checkout_request_id: str,
    ) -> dict[str, Any]:
        """Query the status of an STK Push transaction.

        Args:
            shortcode: Business shortcode used in the STK Push.
            passkey: Lipa Na M-PESA passkey.
            checkout_request_id: CheckoutRequestID from the STK Push response.

        Returns:
            API response with transaction status.

        Raises:
            APIError: If the API request fails.
        """
        timestamp = generate_timestamp()
        password = generate_password(shortcode, passkey, timestamp)

        payload = {
            "BusinessShortCode": shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id,
        }

        return self._request("stk_query", payload)

    # =========================================================================
    # Customer to Business (C2B)
    # =========================================================================

    def c2b_register_urls(
        self,
        shortcode: str,
        confirmation_url: str,
        validation_url: str,
        response_type: str = "Completed",
    ) -> dict[str, Any]:
        """Register C2B validation and confirmation URLs.

        Args:
            shortcode: Business shortcode.
            confirmation_url: URL for payment confirmation callbacks.
            validation_url: URL for payment validation callbacks.
            response_type: "Completed" or "Cancelled".

        Returns:
            API response confirming registration.

        Raises:
            APIError: If the API request fails.
        """
        payload = {
            "ShortCode": shortcode,
            "ResponseType": response_type,
            "ConfirmationURL": confirmation_url,
            "ValidationURL": validation_url,
        }

        return self._request("c2b_register", payload)

    def c2b_simulate(
        self,
        shortcode: str,
        phone: str,
        amount: int,
        bill_ref_number: str = "",
        command_id: str = "CustomerPayBillOnline",
    ) -> dict[str, Any]:
        """Simulate a C2B transaction (sandbox only).

        Args:
            shortcode: Business shortcode.
            phone: Customer's phone number.
            amount: Transaction amount.
            bill_ref_number: Bill reference number (account number).
            command_id: "CustomerPayBillOnline" or "CustomerBuyGoodsOnline".

        Returns:
            API response confirming simulation.

        Raises:
            ValidationError: If not in sandbox environment.
            APIError: If the API request fails.
        """
        if self.env != Environment.SANDBOX:
            raise ValidationError(
                "C2B simulation is only available in sandbox environment"
            )

        phone_formatted = format_phone_number(phone)

        payload = {
            "ShortCode": shortcode,
            "CommandID": command_id,
            "Amount": amount,
            "Msisdn": phone_formatted,
            "BillRefNumber": bill_ref_number,
        }

        return self._request("c2b_simulate", payload)

    # =========================================================================
    # Business to Customer (B2C)
    # =========================================================================

    def b2c_payment(
        self,
        initiator_name: str,
        security_credential: str,
        shortcode: str,
        phone: str,
        amount: int,
        result_url: str,
        timeout_url: str,
        command_id: str = "BusinessPayment",
        remarks: str = "",
        occasion: str = "",
    ) -> dict[str, Any]:
        """Make a B2C (Business to Customer) payment.

        Args:
            initiator_name: API initiator username.
            security_credential: Encrypted security credential.
            shortcode: Business shortcode making the payment.
            phone: Recipient's phone number.
            amount: Amount to send.
            result_url: URL for result notification.
            timeout_url: URL for timeout notification.
            command_id: "BusinessPayment", "SalaryPayment", or "PromotionPayment".
            remarks: Comments about the transaction.
            occasion: Optional occasion description.

        Returns:
            API response with transaction details.

        Raises:
            APIError: If the API request fails.
        """
        phone_formatted = format_phone_number(phone)

        payload = {
            "InitiatorName": initiator_name,
            "SecurityCredential": security_credential,
            "CommandID": command_id,
            "Amount": amount,
            "PartyA": shortcode,
            "PartyB": phone_formatted,
            "Remarks": remarks,
            "QueueTimeOutURL": timeout_url,
            "ResultURL": result_url,
            "Occasion": occasion,
        }

        return self._request("b2c_payment", payload)

    # =========================================================================
    # Business to Business (B2B)
    # =========================================================================

    def b2b_payment(
        self,
        initiator_name: str,
        security_credential: str,
        sender_shortcode: str,
        receiver_shortcode: str,
        amount: int,
        result_url: str,
        timeout_url: str,
        command_id: str = "BusinessPayBill",
        account_reference: str = "",
        remarks: str = "",
        requester: str = "",
    ) -> dict[str, Any]:
        """Make a B2B (Business to Business) payment.

        Args:
            initiator_name: API initiator username.
            security_credential: Encrypted security credential.
            sender_shortcode: Shortcode sending the payment.
            receiver_shortcode: Shortcode receiving the payment.
            amount: Amount to send.
            result_url: URL for result notification.
            timeout_url: URL for timeout notification.
            command_id: "BusinessPayBill" or "MerchantToMerchantTransfer".
            account_reference: Account reference for the payment.
            remarks: Comments about the transaction.
            requester: Phone number of the requester (optional).

        Returns:
            API response with transaction details.

        Raises:
            APIError: If the API request fails.
        """
        payload = {
            "Initiator": initiator_name,
            "SecurityCredential": security_credential,
            "CommandID": command_id,
            "SenderIdentifierType": "4",
            "ReceiverIdentifierType": "4",
            "Amount": amount,
            "PartyA": sender_shortcode,
            "PartyB": receiver_shortcode,
            "AccountReference": account_reference,
            "Remarks": remarks,
            "QueueTimeOutURL": timeout_url,
            "ResultURL": result_url,
        }

        if requester:
            payload["Requester"] = requester

        return self._request("b2b_payment", payload)

    # =========================================================================
    # Transaction Status
    # =========================================================================

    def transaction_status(
        self,
        initiator_name: str,
        security_credential: str,
        shortcode: str,
        transaction_id: str,
        result_url: str,
        timeout_url: str,
        remarks: str = "Transaction status query",
        occasion: str = "",
    ) -> dict[str, Any]:
        """Query the status of a transaction.

        Args:
            initiator_name: API initiator username.
            security_credential: Encrypted security credential.
            shortcode: Business shortcode.
            transaction_id: M-PESA transaction ID to query.
            result_url: URL for result notification.
            timeout_url: URL for timeout notification.
            remarks: Comments about the query.
            occasion: Optional occasion description.

        Returns:
            API response with transaction status.

        Raises:
            APIError: If the API request fails.
        """
        payload = {
            "Initiator": initiator_name,
            "SecurityCredential": security_credential,
            "CommandID": "TransactionStatusQuery",
            "TransactionID": transaction_id,
            "PartyA": shortcode,
            "IdentifierType": "4",
            "ResultURL": result_url,
            "QueueTimeOutURL": timeout_url,
            "Remarks": remarks,
            "Occasion": occasion,
        }

        return self._request("transaction_status", payload)

    # =========================================================================
    # Account Balance
    # =========================================================================

    def account_balance(
        self,
        initiator_name: str,
        security_credential: str,
        shortcode: str,
        result_url: str,
        timeout_url: str,
        remarks: str = "Balance query",
    ) -> dict[str, Any]:
        """Query the balance of an M-PESA account.

        Args:
            initiator_name: API initiator username.
            security_credential: Encrypted security credential.
            shortcode: Business shortcode to query.
            result_url: URL for result notification.
            timeout_url: URL for timeout notification.
            remarks: Comments about the query.

        Returns:
            API response confirming the query request.

        Raises:
            APIError: If the API request fails.
        """
        payload = {
            "Initiator": initiator_name,
            "SecurityCredential": security_credential,
            "CommandID": "AccountBalance",
            "PartyA": shortcode,
            "IdentifierType": "4",
            "ResultURL": result_url,
            "QueueTimeOutURL": timeout_url,
            "Remarks": remarks,
        }

        return self._request("account_balance", payload)

    # =========================================================================
    # Reversal
    # =========================================================================

    def reversal(
        self,
        initiator_name: str,
        security_credential: str,
        shortcode: str,
        transaction_id: str,
        amount: int,
        result_url: str,
        timeout_url: str,
        remarks: str = "Reversal request",
        occasion: str = "",
    ) -> dict[str, Any]:
        """Reverse a completed M-PESA transaction.

        Args:
            initiator_name: API initiator username.
            security_credential: Encrypted security credential.
            shortcode: Business shortcode that received the payment.
            transaction_id: M-PESA transaction ID to reverse.
            amount: Amount to reverse.
            result_url: URL for result notification.
            timeout_url: URL for timeout notification.
            remarks: Comments about the reversal.
            occasion: Optional occasion description.

        Returns:
            API response confirming the reversal request.

        Raises:
            APIError: If the API request fails.
        """
        payload = {
            "Initiator": initiator_name,
            "SecurityCredential": security_credential,
            "CommandID": "TransactionReversal",
            "TransactionID": transaction_id,
            "Amount": amount,
            "ReceiverParty": shortcode,
            "ReceiverIdentifierType": "4",
            "ResultURL": result_url,
            "QueueTimeOutURL": timeout_url,
            "Remarks": remarks,
            "Occasion": occasion,
        }

        return self._request("reversal", payload)

    # =========================================================================
    # Tax Remittance
    # =========================================================================

    def tax_remittance(
        self,
        initiator_name: str,
        security_credential: str,
        sender_shortcode: str,
        amount: int,
        account_reference: str,
        result_url: str,
        timeout_url: str,
        kra_shortcode: str = "572572",
        remarks: str = "Tax remittance",
    ) -> dict[str, Any]:
        """Remit tax to the Kenya Revenue Authority (KRA).

        Args:
            initiator_name: API initiator username.
            security_credential: Encrypted security credential.
            sender_shortcode: Business shortcode remitting the tax.
            amount: Tax amount to remit.
            account_reference: Payment Registration Number (PRN).
            result_url: URL for result notification.
            timeout_url: URL for timeout notification.
            kra_shortcode: KRA paybill number (default: 572572).
            remarks: Comments about the remittance.

        Returns:
            API response confirming the remittance request.

        Raises:
            APIError: If the API request fails.
        """
        payload = {
            "Initiator": initiator_name,
            "SecurityCredential": security_credential,
            "CommandID": "PayTaxToKRA",
            "SenderIdentifierType": "4",
            "ReceiverIdentifierType": "4",
            "Amount": amount,
            "PartyA": sender_shortcode,
            "PartyB": kra_shortcode,
            "AccountReference": account_reference,
            "Remarks": remarks,
            "QueueTimeOutURL": timeout_url,
            "ResultURL": result_url,
        }

        return self._request("tax_remittance", payload)

    # =========================================================================
    # Dynamic QR
    # =========================================================================

    def dynamic_qr(
        self,
        merchant_name: str,
        ref_no: str,
        amount: int,
        shortcode: str,
        transaction_type: str = "BG",
        size: str = "300",
    ) -> dict[str, Any]:
        """Generate a dynamic M-PESA QR code.

        Args:
            merchant_name: Name of the merchant.
            ref_no: Transaction reference number.
            amount: Amount for the QR code.
            shortcode: Credit Party Identifier (Paybill/Till).
            transaction_type: "BG" (Buy Goods), "PB" (Pay Bill),
                "SM" (Send Money), "SB" (Send to Business), "WA" (Withdraw Agent).
            size: Size of the QR image in pixels.

        Returns:
            API response with QR code data.

        Raises:
            APIError: If the API request fails.
        """
        payload = {
            "MerchantName": merchant_name,
            "RefNo": ref_no,
            "Amount": amount,
            "TrxCode": transaction_type,
            "CPI": shortcode,
            "Size": size,
        }

        return self._request("dynamic_qr", payload)
