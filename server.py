"""
Unified MCP Server's integration.

"""

import json
from typing import Optional, Dict, Any, List, Annotated
from pydantic import BaseModel, Field

import httpx  # Use an async HTTP client
from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError


# Create the FastMCP server instance
mcp = FastMCP(
    name="UnifiedMCPServer",
    instructions="""
    This server provides tools to interact with scheduling APIs for checking availability and creating bookings.
    
    Available tools:
    - get_availability: Get available slots for scheduling a meeting, when the user wants booking.
    - create_booking: Create a booking for a meeting according to the available slot.
    """
)

EVERGEN_AVAILABILITY_URL = "https://api.scheduling.narwh.ai/availability"
EVERGEN_BOOKING_URL = "https://api.scheduling.narwh.ai/bookings"
DEFAULT_TENANT = "evergen-systems-ltd"
DEFAULT_EVENT_TYPE = "73dd9f9a-e7b8-4b28-94c8-260458497f18"


# Pydantic models for booking request
class BookingSlot(BaseModel):
    """Defines the time window for the booking."""
    start: str = Field(
        ...,
        description="Starting time of the meeting. Must be in ISO 8601 format (e.g., '2025-09-25T04:15:00.000Z')"
    )


class BookingLocation(BaseModel):
    """Location of the meeting address and postcode."""
    postcode: str = Field(
        ...,
        description="Postcode of the invitee (e.g., 'SW1A 2AA')"
    )
    address: str = Field(
        ...,
        description="Address of the invitee (e.g., '10 Downing Street, London')"
    )


class BookingInvitee(BaseModel):
    """Details of an invitee."""
    email: str = Field(
        ...,
        description="Email of the invitee"
    )
    name: str = Field(
        ...,
        description="Name of the invitee"
    )


@mcp.tool(
    name="get_availability",
    description="Use this tool to get available slots from the scheduling, when the user wants booking.",
)
async def get_availability(
    tenantId: Annotated[str, Field(description="The tenant identifier, defaulting to 'evergen-systems-ltd'")] = DEFAULT_TENANT,
    eventTypeId: Annotated[str, Field(description="The event type identifier, defaulting to '73dd9f9a-e7b8-4b28-94c8-260458497f18'")] = DEFAULT_EVENT_TYPE,
    timeout: int = 120,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Get available slots for scheduling a meeting, when the user wants booking.
    """
    # Log via context if available
    if ctx is not None:
        await ctx.info(f"Requesting availability for tenant={tenantId}, eventType={eventTypeId}")

    headers = {
        "Content-Type": "application/json",
        "x-tenant-id": tenantId,
    }
    body = {
        "tenantId": tenantId,
        "eventTypeId": eventTypeId,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(EVERGEN_AVAILABILITY_URL, headers=headers, json=body)
    except httpx.RequestError as e:
        raise ToolError(f"Network error when calling availability API: {e}")

    if resp.status_code >= 400:
        # Try to parse error body
        detail = None
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise ToolError(f"API returned {resp.status_code}: {detail}")

    try:
        data = resp.json()
    except json.JSONDecodeError as e:
        raise ToolError(f"Response is not valid JSON: {e}")

    # Optionally report progress
    if ctx is not None:
        await ctx.info("Received availability response")

    return data


@mcp.tool(
    name="create_booking",
    description="Use this function to make booking for a meeting according to the available slot.",
)
async def create_booking(
    slotToken: Annotated[str, Field(description="slotToken needs to be taken from previous tool get_availability. It must be same slot token of the slot you're using.")],
    slot: BookingSlot,
    location: BookingLocation,
    invitees: Annotated[List[BookingInvitee], Field(description="Invitees details should be listed like name and email.")],
    eventTypeId: Annotated[str, Field(description="The event type identifier, defaulting to '73dd9f9a-e7b8-4b28-94c8-260458497f18'")] = DEFAULT_EVENT_TYPE,
    timeout: int = 120,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Create a booking for a meeting according to the available slot.
    """
    # Log via context if available
    if ctx is not None:
        await ctx.info(f"Creating booking with slotToken={slotToken}, eventTypeId={eventTypeId}")

    headers = {
        "Content-Type": "application/json",
        "x-tenant-id": DEFAULT_TENANT,
    }
    body = {
        "slotToken": slotToken,
        "slot": slot.model_dump(),
        "location": location.model_dump(),
        "invitees": [invitee.model_dump() for invitee in invitees],
        "eventTypeId": eventTypeId,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(EVERGEN_BOOKING_URL, headers=headers, json=body)
    except httpx.RequestError as e:
        raise ToolError(f"Network error when calling booking API: {e}")

    if resp.status_code >= 400:
        # Try to parse error body
        detail = None
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise ToolError(f"API returned {resp.status_code}: {detail}")

    try:
        data = resp.json()
    except json.JSONDecodeError as e:
        raise ToolError(f"Response is not valid JSON: {e}")

    # Optionally report progress
    if ctx is not None:
        await ctx.info("Booking created successfully")

    return data


if __name__ == "__main__":
    # Run the server with STDIO transport (default)
    # This is suitable for local MCP clients like Claude Desktop
    mcp.run()