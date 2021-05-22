import os
from functools import lru_cache
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from requests import Session

load_dotenv()

hyperion_base_url = f"{os.getenv('HYPERION_ENDPOINT')}/api/v1"

hyperion_session = Session()
hyperion_session.headers.update(
    {
        "Authorization": f"Bearer {os.getenv('HYPERION_INTEGRATION_TOKEN')}",
    }
)

currency_details = hyperion_session.get(
    f"{hyperion_base_url}/integration/currency"
).json()


@lru_cache()
def resolve_account_id(account_id: str) -> Optional[Dict[str, Any]]:
    account_resp = hyperion_session.get(f"{hyperion_base_url}/accounts/{account_id}")
    if account_resp.status_code == 404:
        return None

    return account_resp.json()
