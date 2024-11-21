# Generated by Django 4.2.7 on 2024-11-20 16:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BreakFast_app', '0004_fastingplan_program_weightlog_userprogram_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='fastingplan',
            name='eating_days',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='fastingplan',
            name='end_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='fastingplan',
            name='fasting_days',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='fastingplan',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='fastingplan',
            name='plan_type',
            field=models.CharField(choices=[('16:8', '16:8 Intermittent Fasting'), ('18:6', '18:6 Intermittent Fasting'), ('20:4', '20:4 Intermittent Fasting'), ('5:2', '5:2 Diet'), ('CUSTOM', 'Custom Plan')], default='16:8', max_length=20),
        ),
        migrations.AddField(
            model_name='fastingplan',
            name='start_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='fastingtracker',
            name='actual_end_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='fastingtracker',
            name='is_paused',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='fastingtracker',
            name='pause_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='fastingtracker',
            name='energy_level',
            field=models.IntegerField(blank=True, choices=[(1, 'Very Low'), (2, 'Low'), (3, 'Medium'), (4, 'High'), (5, 'Very High')], null=True),
        ),
        migrations.AlterField(
            model_name='fastingtracker',
            name='mood',
            field=models.CharField(blank=True, choices=[('GREAT', 'Great'), ('GOOD', 'Good'), ('OKAY', 'Okay'), ('BAD', 'Bad'), ('TERRIBLE', 'Terrible')], max_length=20, null=True),
        ),
    ]
