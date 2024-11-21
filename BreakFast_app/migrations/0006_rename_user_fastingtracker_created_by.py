from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('BreakFast_app', '0005_fastingplan_eating_days_fastingplan_end_date_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='fastingtracker',
            old_name='user',
            new_name='created_by',
        ),
    ]
