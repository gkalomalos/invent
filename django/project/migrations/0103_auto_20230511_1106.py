# Generated by Django 2.1 on 2023-05-24 07:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0102_portfolio_landscape_review'),
    ]

    operations = [
        migrations.AlterField(
            model_name='solution',
            name='is_active',
            field=models.BooleanField(),
        ),
    ]
