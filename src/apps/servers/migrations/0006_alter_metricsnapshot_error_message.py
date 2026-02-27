# Generated for Ruff DJ001 fix - TextField blank/default instead of null

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("servers", "0005_add_cleanup_beat_task"),
    ]

    operations = [
        migrations.AlterField(
            model_name="metricsnapshot",
            name="error_message",
            field=models.TextField(blank=True, default=""),
        ),
    ]
