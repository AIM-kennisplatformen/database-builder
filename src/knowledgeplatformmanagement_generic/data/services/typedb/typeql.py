from abc import ABC, abstractmethod
from datetime import date, datetime
from inspect import getmro, isabstract
from typing import Annotated, Self

from loguru import logger
from pydantic import BaseModel, StringConstraints


class Key[T](BaseModel, frozen=True):
    def __str__(self) -> str:
        return f"{self.title} uniquely identified by its {self.title_key} ‘{self.value_key}’"

    classobject: type[T]
    name_key: Annotated[str, StringConstraints(min_length=1)]
    name_schema: Annotated[str, StringConstraints(min_length=1)]
    # TODO: Use `ClassVar` since this is a class variable. However, Pydantic gets in the way.
    title_key: Annotated[str, StringConstraints(min_length=1)]
    title: Annotated[str, StringConstraints(min_length=1)]
    value_key: Annotated[str, StringConstraints(min_length=1)]


# pylint: disable-next=too-few-public-methods
class TypeqlThing(BaseModel, ABC):
    @abstractmethod
    def nonabstract_marker(self) -> None:
        """Abstract marker to prevent direct instantiation. Override in `TypeqlThing` subclasses that reflect a
        non-abstract thing definition in the schema."""

    def to_key(self) -> Key[Self]:
        """Detects `self`'s key attribute based on its type annotation `'key'`, and returns a `Key` object for `self`.
        `Key` objects are used to associate role players with a relation.

        Raises `ValueError` if no attribute with a key annotation was found."""

        name_key = ""
        for name_field, fieldinfo in self.model_fields.items():
            if fieldinfo.metadata and fieldinfo.metadata[0] == "key":
                name_key = name_field
                if not fieldinfo.title:
                    raise TypeqlThingMissingTitleError(typeqlthing=self)
                title_field = fieldinfo.title
                break
        if not name_key:
            raise TypeqlThingMissingKeyDeclarationError(typeqlthing=self)

        if name_key is not None:
            value_key = getattr(self, name_key)
            return Key(
                classobject=self.__class__,
                title=self.model_config.get("title"),
                title_key=title_field,
                name_key=name_key,
                name_schema=self.__class__.to_typeql_name_schema(),
                value_key=value_key,
            )
        raise ValueError()

    @classmethod
    def to_typeql_name_schema(cls) -> str:
        """
        Names the type after the last non-abstract class, in sub- to superclass order, to preserve generality.
        """
        classname = cls.__name__
        mro = getmro(cls=cls)
        for index, superclass in enumerate(mro):
            if isabstract(superclass):
                # It’s impossible for the first class in the MRO to be abstract, so this index calculation is always
                # positive.
                classname = mro[index - 1].__name__
                break
        return "".join(f"-{character.lower()}" if character.isupper() else character for character in classname).lstrip(
            "-",
        )

    def __str__(self) -> str:
        if (title := self.model_config.get("title", None)) and title:
            description = f"Some {title} "
            if isinstance(self, TypeqlThingRelation):
                description += "relation "
            description += "exists"
            for field, fieldinfo in self.__class__.model_fields.items():
                if getattr(self, field, None):
                    description += ", with "
                    if isinstance(getattr(self, field), Key):
                        description += "role "
                    if not isinstance(getattr(self, field), TypeqlAttribute | Key):
                        description += f"{fieldinfo.title} ‘{getattr(self, field)}’"
                    else:
                        description += f"{getattr(self, field)!s}"
            description += "."
            return description
        # TODO: Specify exception.
        raise ValueError()

    # TODO: The complexity in this function is essential.
    def _to_typeql_attributes(self) -> str:  # noqa: C901, PLR0912
        attributes = []
        for field_current in self.model_fields:
            if (value := getattr(self, field_current)) is None:
                logger.trace("Missing value for field `{field_name}`.", field_name=field_current)
                continue
            if field_current == "value":
                # TODO: Document this.
                # Exempt `value` attribute of `TypeqlAttribute` objects.
                continue
            field_name_typedb = field_current.replace("_", "-")
            has = f"has {field_name_typedb} "
            match value:
                case bool():
                    attributes.append(has + str(value).lower())
                case float() | int():
                    attributes.append(has + str(value))
                case str():
                    if '"' in value:
                        value = value.replace('"', "'")
                    attributes.append(f'{has}"{value}"')
                case list():
                    # TODO: !! Support https://typedb.com/docs/typeql/2.x/queries/insert#_multivalued_attributes
                    if all(isinstance(item, str) for item in value):
                        attributes.append(f'{has}"{", ".join(value)}"')
                    else:
                        msg = f"Unsupported list item type for field {field_name_typedb}."
                        raise TypeError(msg)
                case datetime():
                    attributes.append(has + value.strftime(r"%Y-%m-%dT%H:%M:%S.%f")[:-3])
                case date():
                    attributes.append(has + value.strftime(r"%Y-%m-%d"))
                case Key():
                    continue
                case TypeqlAttribute():
                    attributes.append(has + f"${value.to_typeql_name_schema()}")
                case _:
                    msg = f"Unsupported type for field {field_name_typedb}: {type(value)}."
                    raise TypeError(msg)
        return ", " + (", ".join(attributes)) if attributes else ""

    @abstractmethod
    def to_typeql(self) -> str: ...

    def scan_composite_attributes(self) -> str:
        statements = []
        for field_current in self.model_fields:
            if (value := getattr(self, field_current)) is None:
                continue
            match value:
                case TypeqlAttribute():
                    statements.append(value.to_typeql())
                case _:
                    continue
        return ";\n".join(statements) if statements else ""

    def scan_key_attributes(self) -> tuple[str, list[str]]:
        arguments = []
        statement_match = "match "
        # Match based on keys.
        for index, name_field in enumerate(self.model_fields):
            if (value := getattr(self, name_field)) is None or not isinstance(value, Key):
                continue
            variable = f"$var{index:d}"
            name_attribute_key = f"{value.name_key.replace('_', '-'):s}"
            statement_match += f"{variable} isa {value.name_schema:s}, "
            # TODO: Support non-string-valued keys.
            statement_match += f'has {name_attribute_key:s} "{value.value_key:s}";\n'
            name_attribute = name_field.replace("_", "-")
            arguments.append(f"{name_attribute}: {variable}")
        if statement_match == "match ":
            statement_match = ""
        return (statement_match, arguments)


class TypeqlThingMissingTitleError(TypeError):
    def __init__(self, *, typeqlthing: TypeqlThing) -> None:
        super().__init__(
            f"TypeQL thing {typeqlthing!r} was defined without a `title` attribute in its model config.",
        )


class TypeqlThingMissingKeyDeclarationError(TypeError):
    def __init__(self, *, typeqlthing: TypeqlThing) -> None:
        super().__init__(
            f"TypeQL thing {typeqlthing!r} was defined without a `key` attribute.",
        )


class TypeqlAttribute[T](TypeqlThing):
    value: T

    def __str__(self) -> str:
        if (title := self.model_config.get("title", None)) and title:
            return (
                f"{title} ("
                + ", ".join(
                    f"{value.title} ‘{getattr(self, attribute)}’"
                    for attribute, value in self.__class__.model_fields.items()
                    if getattr(self, attribute, None)
                )
                + ")"
            )
        raise TypeqlThingMissingTitleError(typeqlthing=self)

    # Due to https://peps.python.org/pep-0622/#make-it-an-expression, PLR0911 must be allowed.
    def _to_typeql_placeholder(self) -> str:  # noqa: PLR0911
        match self.value:
            case bool():
                return str(self.value).lower()
            case float() | int():
                return str(self.value)
            case str():
                if '"' in self.value:
                    return self.value.replace('"', "'")
                return f'"{self.value}"'
            case list():
                # TODO: !! Support https://typedb.com/docs/typeql/2.x/queries/insert#_multivalued_attributes
                if all(isinstance(item, str) for item in self.value):
                    return f'"{", ".join(self.value)}"'
                msg = "Unsupported list item type for attribute value."
                raise TypeError(msg)
            case datetime():
                return self.value.strftime(r"%Y-%m-%dT%H:%M:%S.%f")[:-3]
            case date():
                return self.value.strftime(r"%Y-%m-%d")
            case _:
                msg = f"Unsupported type for attribute value: {type(self.value)}."
                raise TypeError(msg)

    def to_typeql(self) -> str:
        name_schema = self.to_typeql_name_schema()
        return (
            f"insert ${name_schema} {self._to_typeql_placeholder()} isa {name_schema}{self._to_typeql_attributes()};\n"
        )


# This is an abstract class and I see no reason to require more than one public method.
# pylint: disable-next=too-few-public-methods
class TypeqlThingRelation(TypeqlThing):
    def to_typeql(self) -> str:
        statement_match, arguments = self.scan_key_attributes()
        if not arguments:
            raise TypeqlThingRelationMissingKeyError(self)
        statement_insert_composite = self.scan_composite_attributes()
        statement_insert = (
            f"insert $_ ({', '.join(arguments)}) isa {self.to_typeql_name_schema()}{self._to_typeql_attributes()};\n"
        )
        return (
            f"{statement_insert_composite}"
            f"{statement_match}"
            f"{'insert' if statement_insert_composite else ''}"
            f"{statement_insert}"
        )


class TypeqlThingRelationMissingKeyError(ValueError):
    def __init__(self, typeqlrelation: TypeqlThingRelation) -> None:
        super().__init__(
            f"TypeQL relation {typeqlrelation!r} was instantiated without a `Key` attribute value, as required to play "
            "roles.",
        )


# This is an abstract class and I see no reason to require more than one public method.
# pylint: disable-next=too-few-public-methods
class TypeqlThingEntity(TypeqlThing):
    def to_typeql(self) -> str:
        statement_match, arguments = self.scan_key_attributes()
        statement_insert_composite = self.scan_composite_attributes()
        statement_insert = f"$_ isa {self.to_typeql_name_schema()}{self._to_typeql_attributes()};\n"
        return (
            f"{statement_insert_composite}"
            f"{statement_match}"
            f"{'' if statement_insert_composite else 'insert '}"
            f"{statement_insert}"
        )
