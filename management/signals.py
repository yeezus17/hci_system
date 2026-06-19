from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Annonce, BuyRequest

@receiver(post_save, sender=Annonce)
def match_new_annonce_to_buyers(sender, instance, created, **kwargs):
    if created and instance.status == 'published':
        # Find buyers looking for this specific category and city
        matches = BuyRequest.objects.filter(
            category_wanted=instance.type_bien,
            ville__iexact=instance.ville,
            max_budget__gte=instance.prix
        )
        
        for match in matches:
            # Here you would trigger an email or notification
            print(f"Match found! Notify user: {match.user.username}")