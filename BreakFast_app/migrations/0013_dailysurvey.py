# Generated by Django 4.2.7 on 2024-11-23 08:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('BreakFast_app', '0012_delete_sleeplog'),
    ]

    operations = [
        migrations.CreateModel(
            name='DailySurvey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('hours_of_sleep', models.FloatField()),
                ('mood', models.IntegerField(choices=[(1, 'Bad'), (2, 'Okay'), (3, 'Good')])),
                ('energy_level', models.IntegerField(choices=[(1, 'Low'), (2, 'Medium'), (3, 'High')])),
                ('stress_level', models.IntegerField(choices=[(1, 'Low'), (2, 'Medium'), (3, 'High')])),
                ('hunger_level', models.IntegerField(choices=[(1, 'Low'), (2, 'Medium'), (3, 'High')])),
                ('notes', models.TextField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date'],
                'unique_together': {('user', 'date')},
            },
        ),
    ]
