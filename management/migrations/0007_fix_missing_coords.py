from django.db import migrations, models # Ensure this is the only models import

class Migration(migrations.Migration):

    dependencies = [
        ('management', '0006_remove_service_price_start_profile_user_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='annonce',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='annonce',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
    ]