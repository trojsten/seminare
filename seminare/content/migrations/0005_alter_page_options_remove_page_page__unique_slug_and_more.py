# Generated by Django 5.1.4 on 2025-07-07 12:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0004_alter_menuitem_url"),
        ("contests", "0003_delete_category"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="page",
            options={"ordering": ["contest", "slug"]},
        ),
        migrations.RemoveConstraint(
            model_name="page",
            name="page__unique_slug",
        ),
        migrations.RemoveField(
            model_name="menugroup",
            name="site",
        ),
        migrations.RemoveField(
            model_name="page",
            name="site",
        ),
        migrations.AddField(
            model_name="menugroup",
            name="contest",
            field=models.ForeignKey(
                default=3,
                on_delete=django.db.models.deletion.CASCADE,
                to="contests.contest",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="page",
            name="contest",
            field=models.ForeignKey(
                default=3,
                on_delete=django.db.models.deletion.CASCADE,
                to="contests.contest",
            ),
            preserve_default=False,
        ),
        migrations.AddConstraint(
            model_name="page",
            constraint=models.UniqueConstraint(
                models.F("contest"), models.F("slug"), name="page__unique_slug"
            ),
        ),
    ]
