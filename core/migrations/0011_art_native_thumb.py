# Generated by Django 3.2 on 2021-05-11 08:58

from django.db import migrations
from django.db import models

import core.models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_auto_20210507_1147"),
    ]

    operations = [
        migrations.AddField(
            model_name="art",
            name="native_thumb",
            field=models.TextField(default="", validators=[core.models.validate_text]),
            preserve_default=False,
        ),
    ]
