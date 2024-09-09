from pydantic import Secret
from pydantic.functional_validators import BeforeValidator


from typing import Annotated


def make_whole_number(value: float) -> int:
    """Remove digits after the decimal point of a float value.

    Examples:
      >>> make_whole_number(44.560)
      44
      >>> make_whole_number(856.9785623)
      856
      >>> make_whole_number(9999.99)
      9999

    Args:
      value: value to be converted to an int

    Returns:
      The value as an integer, never rounded up.
    """
    return int(value)


WholeDollar = Annotated[float, BeforeValidator(make_whole_number)]


class SSN(Secret[str]):
    def _display(self) -> str:
        return "***-**-****"
