from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("maps", "0002_map"),
    ]

    operations = [
        migrations.RenameField(
            model_name="map",
            old_name="map_img",
            new_name="head_img",
        ),
        migrations.AddField(
            model_name="map",
            name="map_img",
            field=models.ImageField(blank=True, null=True, upload_to="maps/"),
        ),
    ]
