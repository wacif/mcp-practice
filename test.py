import requests
import json

CAL_API_KEY = "cal_live_e00de05fa6917e25a12c489b73b6dd87"

def Get_Available_Slots(startTime: str, endTime: str, eventTypeSlug: str, eventTypeId: str) -> str:
    """
    Get available meeting slots from the Cal.com API.
    """
    url = "https://api.cal.com/v2/slots"
    headers = {
        "cal-api-version": "2024-08-13",
        "Content-Type": "application/json",
        "Authorization": "Bearer " + CAL_API_KEY
    }

    params = {
        "startTime": startTime,
        "endTime": endTime,
        "eventTypeSlug": eventTypeSlug,
        "eventTypeId": eventTypeId
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30
        )
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        return json.dumps({
            "error": True,
            "message": f"Failed to get available meeting slots. Error: {str(e)}"
        })

print(Get_Available_Slots("2025-10-04", "2025-10-06", "meeting", "1945594"))