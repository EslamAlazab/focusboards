from django.contrib.postgres.operations import CreateExtension
from django.db import migrations


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        # This migration should run first, so it should not have dependencies on its own app.
    ]

    operations = [
        CreateExtension("vector"), # enabling pgvector extension.
    ]
