from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.db import models
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_approved_editor = models.BooleanField(default=False)
    # Updated to match the signup form field
    phone_number = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')
    bio = models.TextField(max_length=500, blank=True)
    
    # New Field: Track if they are a 'Prestataire' or 'Matière' user type
    user_type = models.CharField(max_length=20, choices=[
        ('client', 'Client'),
        ('partner', 'Partenaire HCI')
    ], default='client')

    def __str__(self):
        return f"Profile de {self.user.username}"

# --- SIGNALS (Keep these as they are essential for your signup view) ---
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Category(models.Model):
    SERVICE_TYPES = [
        ('prestataire', 'Prestataire (Expert/Artisan)'),
        ('matiere', 'Matière (Matériaux/Fournitures)'),
    ]
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=SERVICE_TYPES)
    # Updated with a more specific default for your aesthetic
    icon_class = models.CharField(max_length=50, default="fa-solid fa-cube", 
                                help_text="FontAwesome class (ex: fa-helmet-safety)")

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})" 

class Service(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='services')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='services')
    
    name = models.CharField(max_length=200, verbose_name="Nom de l'entreprise")
    description = models.TextField()
    logo = models.ImageField(upload_to='services/logos/', blank=True, null=True)
    
    city = models.CharField(max_length=100, default="Casablanca")
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20)
    website = models.URLField(blank=True)
    
    # NEW: Matching the 'Boosté' badge logic from our Marketplace UI
    is_boosted = models.BooleanField(default=False, help_text="Affiche le badge Fusée Orange")
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.category.name if self.category else 'Sans Catégorie'}"

class Annonce(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('published', 'Publiée'),
        ('archived', 'Archivée'),
    ]

    # Added to match your Sidebar links
    TRANSACTION_CHOICES = [
        ('ACHAT', 'Achat'),
        ('VENTE', 'Vente'),
        ('LOCATION', 'Location'),
    ]

    # Added to match your Filter Tiles
    TYPE_CHOICES = [
        ('VILLA', 'Villa'),
        ('APPARTEMENT', 'Appartement'),
        ('TERRAIN', 'Terrain'),
        ('BUREAU', 'Bureau'),
    ]

    auteur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='annonces')
    titre = models.CharField(max_length=200)
    
    # New Field: Transaction Type
    type_transaction = models.CharField(
        max_length=20, 
        choices=TRANSACTION_CHOICES, 
        default='ACHAT'
    )
    
    # Updated Field: Type of Property
    type_bien = models.CharField(
        max_length=50, 
        choices=TYPE_CHOICES
    )
    
    ville = models.CharField(max_length=100, default="Maroc")
    prix = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField()
    #image = models.ImageField(upload_to='annonces/%Y/%m/', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    date_pub = models.DateTimeField(auto_now_add=True)
    
    # Geo-location
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return f"{self.titre} ({self.get_type_transaction_display()})"

class AnnonceMedia(models.Model):
    annonce = models.ForeignKey(Annonce, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(upload_to='annonces/media/')
    is_video = models.BooleanField(default=False)

    def __str__(self):
        return f"Media for {self.annonce.titre}"