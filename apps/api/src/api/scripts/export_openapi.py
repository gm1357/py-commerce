"""Write the OpenAPI schema to apps/api/openapi.json (input for packages/api-client)."""

import json
from pathlib import Path

from api.main import app

OUTPUT = Path(__file__).resolve().parents[3] / "openapi.json"


def main() -> None:
    OUTPUT.write_text(json.dumps(app.openapi(), indent=2) + "\n")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
