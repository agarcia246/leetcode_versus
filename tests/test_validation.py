import pytest

from app.domain.backend.models import CreateRoomModel
from app.domain.backend.services import validate_room_settings


def room_model():
    return CreateRoomModel(
        host_username="alex",
        duration=30,
        problem_count=3,
        difficulty="Easy",
        topics=["Array"],
    )


def test_valid_room_settings():
    validate_room_settings(room_model())


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("duration", 500, "duration must be between 1 and 180 minutes"),
        ("problem_count", 0, "problem_count must be between 1 and 10"),
        ("difficulty", "Boss", "difficulty must be Easy, Medium, or Hard"),
        ("topics", [], "at least one topic is required"),
    ],
)
def test_invalid_room_settings(field, value, message):
    model = room_model()
    setattr(model, field, value)

    with pytest.raises(ValueError, match=message):
        validate_room_settings(model)
