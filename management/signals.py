from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import Annonce, BuyRequest

@receiver(pre_save, sender=Annonce)
def track_status_change(sender, instance, **kwargs):
    """
    Caches the original status from the database before it gets overwritten,
    allowing us to detect a state transition in post_save (e.g., draft -> published).
    """
    if instance.pk:
        try:
            old_instance = Annonce.objects.get(pk=instance.pk)
            instance._original_status = old_instance.status
        except Annonce.DoesNotExist:
            instance._original_status = None
    else:
        instance._original_status = None

@receiver(post_save, sender=Annonce)
def match_new_annonce_to_buyers(sender, instance, created, **kwargs):
    # Trigger if it's a brand new published item, OR if an existing item's status just flipped to 'published'
    status_flipped = not created and getattr(instance, '_original_status', None) != 'published' and instance.status == 'published'
    
    if (created and instance.status == 'published') or status_flipped:
        # FIXED: Changed max_budget__gte to budget_maximum__gte to match your database field
        matches = BuyRequest.objects.filter(
            category_wanted=instance.type_bien,
            ville__iexact=instance.ville,
            budget_maximum__gte=instance.prix
        ).select_related('user')
        
        for match in matches:
            if match.user.email:
                # Dynamically construct the single listing detail absolute URL safely
                site_url = getattr(settings, 'SITE_URL', 'https://hcisystem-production.up.railway.app')
                annonce_url = f"{site_url}/fr/annonces/{instance.id}/"

                context = {
                    'username': match.user.username,
                    'annonce_title': getattr(instance, 'titre', 'Nouvelle Propriété'),
                    'prix': instance.prix,
                    'ville': instance.ville,
                    'url': annonce_url
                }
                
                try:
                    html_message = render_to_string('management/emails/match_alert.html', context)
                    plain_message = strip_tags(html_message)
                    
                    send_mail(
                        subject="✨ Nouvelle opportunité trouvée | HCI Handassa",
                        message=plain_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[match.user.email],
                        html_message=html_message,
                        fail_silently=True,
                    )
                except Exception as e:
                    # Ensures email runtime hitches don't block core DB entry commits
                    print(f"Failed to send email to {match.user.username}: {e}")