# Generated by Django 4.0.3 on 2022-07-21 02:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('analyze', '0011_alter_dataset_catalog_word_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='word',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='analyze.word'),
        ),
    ]