# Generated by Django 3.1.5 on 2021-09-03 04:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loanApp', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='loanrequest',
            name='category',
        ),
        migrations.RemoveField(
            model_name='loanrequest',
            name='is_approved',
        ),
        migrations.AddField(
            model_name='loanrequest',
            name='status',
            field=models.CharField(default='Pending', max_length=100),
        ),
    ]