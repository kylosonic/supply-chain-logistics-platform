from pydantic import BaseModel


class IngestionResult(BaseModel):
    records_processed: int
    records_created: int
    records_updated: int
    errors: list[str]
