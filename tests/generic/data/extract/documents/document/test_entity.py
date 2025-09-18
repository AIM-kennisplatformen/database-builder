from pytest import mark, param

from knowledgeplatformmanagement_generic.data.extract.documents.document import Entity, Entitytype


@mark.parametrize(
    "entitytype,value,repr_expected",
    [
        # Happy path: standard entity creation.
        param("PERSON", "John Doe", "Entity(entitytype='PERSON', value='John Doe')", id="standard_person_entity"),
        # Edge case: empty value.
        param("ORG", "", "Entity(entitytype='ORG', value='')", id="empty_value_entity"),
        # Edge case: special characters.
        param("LOC", "New York!", "Entity(entitytype='LOC', value='New York!')", id="special_chars_entity"),
    ],
)
def test_entity_creation_and_properties(entitytype: Entitytype, value: str, repr_expected: str) -> None:
    entity = Entity(entitytype=entitytype, value=value)
    assert entity.entitytype == entitytype
    assert entity.value == value
    assert repr(entity) == repr_expected


@mark.parametrize(
    "entity_1,entity_2,comparison_expected",
    [
        # Comparison tests.
        param(
            Entity(entitytype="PERSON", value="John"),
            Entity(entitytype="PERSON", value="John"),
            True,
            id="identical_entities_equal",
        ),
        param(
            Entity(entitytype="PERSON", value="John"),
            Entity(entitytype="PERSON", value="Jane"),
            False,
            id="different_values_not_equal",
        ),
        param(
            Entity(entitytype="PERSON", value="John"),
            Entity(entitytype="ORG", value="John"),
            False,
            id="different_types_not_equal",
        ),
    ],
)
def test_entity_comparison(*, entity_1: Entity, entity_2: Entity, comparison_expected: bool) -> None:
    assert (entity_1 == entity_2) == comparison_expected
