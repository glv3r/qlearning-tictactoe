from dataclasses import dataclass


@dataclass
class History:
    mark: str
    board: tuple[str, ...]
    action: int