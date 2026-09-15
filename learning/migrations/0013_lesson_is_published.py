from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0012_remove_lesson_hint_seconds_default'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='is_published',
            field=models.BooleanField(default=True, help_text='Locked (unticked) lessons are invisible to the student.'),
        ),
    ]
