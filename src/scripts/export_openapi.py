"""Export the FastAPI OpenAPI schema to the checked-in frontend contract."""

import json
from pathlib import Path

from src.main import app


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    output_path = project_root / "docs" / "openapi.json"
    output_path.write_text(
        json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Exported OpenAPI schema to {output_path}")


if __name__ == "__main__":
    main()
