from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Annonce, BuyRequest

@receiver(post_save, sender=Annonce)
def match_new_annonce_to_buyers(sender, instance, created, **kwargs):
    if created and instance.status == 'published':
        # Optimization: select_related('user') fetches user metadata in a single JOIN query
        matches = BuyRequest.objects.filter(
            category_wanted=instance.type_bien,
            ville__iexact=instance.ville,
            max_budget__gte=instance.prix
        ).select_related('user')
        
        for match in matches:
            if match.user.email:
                # Dynamic payload context for the email template
                context = {
                    'username': match.user.username,
                    'annonce_title': getattr(instance, 'titre', 'Nouvelle Annonce'), # Falls back to static string if field name varies
                    'prix': instance.prix,
                    'ville': instance.ville,
                    'annonce_id': instance.id
                }
                
                # Render clean HTML layout and generate a plain-text fallback version
                try:
                    html_message = render_to_string('management/emails/match_alert.html', context)
                    plain_message = strip_tags(html_message)
                    
                    send_mail(
                        subject="✨ Nouvelle opportunité trouvée | HCI Handassa",
                        message=plain_message,
                        from_email="noreply@hcisystem.com",
                        recipient_list=[match.user.email],
                        html_message=html_message,
                        fail_silently=True,
                    )
                except Exception as e:
                    # Prevents email failures from crashing the core Annonce save process loop
                    print(f"Failed to send match email notification to {match.user.username}: {e}")