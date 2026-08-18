import jsonschema
from typing import Dict, Any, Tuple

DOC_ITEM_SCHEMA = {
    "type": "object",
    "required": ["url", "title", "body_md", "scraped_at"],
    "properties": {
        "url": {
            "type": "string",
            "pattern": "^https?://"
        },
        "title": {
            "type": "string",
            "minLength": 1
        },
        "body_md": {
            "type": ["string", "null"]
        },
        "scraped_at": {
            "type": "string"
        },
        "category": {
            "type": "string"
        },
        "license": {
            "type": "string"
        }
    }
}

class ItemValidator:
    """Validates DocItem records against defined JSON Schema."""

    @staticmethod
    def validate_item(item_dict: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validates item dictionary against schema.
        Returns (is_valid, error_message).
        """
        try:
            jsonschema.validate(instance=item_dict, schema=DOC_ITEM_SCHEMA)
            return True, ""
        except jsonschema.ValidationError as err:
            return False, str(err)
        except Exception as err:
            return False, str(err)
