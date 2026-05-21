from uuid import uuid4

from django.db import migrations


BOARD_MEMBER_NAME = "Panhary Soeu"
BOARD_MEMBER_ROLE = "General Board Member"


def _stream_raw_data(stream_value):
    raw_data = getattr(stream_value, "raw_data", None)
    if raw_data is not None:
        return list(raw_data)

    data = []
    for block in stream_value:
        value = dict(block.value)
        image = value.get("image")
        if hasattr(image, "pk"):
            value["image"] = image.pk
        data.append({
            "type": block.block_type,
            "value": value,
            "id": str(uuid4()),
        })
    return data


def add_board_member(apps, schema_editor):
    BoardPage = apps.get_model("a_about", "BoardPage")

    for page in BoardPage.objects.filter(slug="board"):
        directors = _stream_raw_data(page.directors)
        if any(
            item.get("type") == "director"
            and item.get("value", {}).get("name") == BOARD_MEMBER_NAME
            for item in directors
        ):
            continue

        directors.append({
            "type": "director",
            "value": {
                "image": None,
                "name": BOARD_MEMBER_NAME,
                "role": BOARD_MEMBER_ROLE,
                "bio": "",
            },
            "id": str(uuid4()),
        })
        page.directors = directors
        page.save(update_fields=["directors"])


def remove_board_member(apps, schema_editor):
    BoardPage = apps.get_model("a_about", "BoardPage")

    for page in BoardPage.objects.filter(slug="board"):
        directors = [
            item
            for item in _stream_raw_data(page.directors)
            if not (
                item.get("type") == "director"
                and item.get("value", {}).get("name") == BOARD_MEMBER_NAME
            )
        ]
        page.directors = directors
        page.save(update_fields=["directors"])


class Migration(migrations.Migration):

    dependencies = [
        ("a_about", "0008_faqpage"),
    ]

    operations = [
        migrations.RunPython(add_board_member, remove_board_member),
    ]
