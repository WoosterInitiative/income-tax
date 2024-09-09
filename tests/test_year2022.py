from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.pytest_plugin import register_fixture

from income_tax.models.year2022 import Form8962


class Form8962Factory(ModelFactory[Form8962]): ...


form_8962_fixture = register_fixture(Form8962Factory)


def test_form_8962(form_8962: Form8962Factory) -> None:
    form_instance = form_8962.build()

    assert isinstance(form_instance.name_on_return, str)
