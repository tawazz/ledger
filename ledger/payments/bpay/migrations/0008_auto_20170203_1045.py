# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-03 02:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bpay', '0007_auto_20170106_1600'),
    ]

    operations = [
        migrations.AddField(
            model_name='bpaytransaction',
            name='biller_code',
            field=models.CharField(default=135111, max_length=10),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='bpaytransaction',
            name='car',
            field=models.CharField(blank=True, help_text=b'Customer Additional Reference.', max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='bpaytransaction',
            name='country',
            field=models.CharField(blank=True, help_text=b'Country of payment.', max_length=3, null=True),
        ),
        migrations.AlterField(
            model_name='bpaytransaction',
            name='discretionary_data',
            field=models.CharField(blank=True, help_text=b'Reason for refund or reversal.', max_length=50, null=True),
        ),
    ]
