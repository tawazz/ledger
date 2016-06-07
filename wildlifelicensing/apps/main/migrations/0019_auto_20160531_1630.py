# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-31 08:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0018_wildlifelicence_return_frequency'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wildlifelicence',
            name='return_frequency',
            field=models.IntegerField(choices=[(-1, 'One off'), (1, 'Monthly'), (3, 'Quarterly'), (6, 'Twice-Yearly'), (12, 'Yearly')], default=-1),
        ),
    ]