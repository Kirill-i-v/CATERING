# Generated by Django 5.1.5 on 2025-04-12 20:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Dish',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, null=True)),
                ('price', models.IntegerField()),
            ],
            options={
                'verbose_name_plural': 'dishes',
                'db_table': 'dishes',
            },
        ),
        migrations.CreateModel(
            name='ExternalOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(max_length=20)),
                ('external_id', models.CharField(max_length=100, unique=True)),
                ('status', models.CharField(max_length=50)),
            ],
            options={
                'db_table': 'external_orders',
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(max_length=20)),
                ('provider', models.CharField(blank=True, max_length=20, null=True)),
                ('eta', models.DateField()),
            ],
            options={
                'db_table': 'orders',
            },
        ),
        migrations.CreateModel(
            name='Restaurant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('address', models.CharField(blank=True, max_length=100)),
            ],
            options={
                'db_table': 'restaurants',
            },
        ),
        migrations.CreateModel(
            name='DishOrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.SmallIntegerField()),
                ('dish', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='food.dish')),
            ],
            options={
                'db_table': 'dish_order_items',
            },
        ),
    ]
