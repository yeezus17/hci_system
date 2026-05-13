from django.contrib import admin
from .models import Annonce
from .models import Profile    
from .models import Category, Service                                                             

@admin.register(Annonce)
class AnnonceAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type_bien', 'prix', 'date_pub')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_approved_editor', 'phone_number')
    list_filter = ('is_approved_editor',)
    search_fields = ('user__username', 'phone_number')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'icon_class')
    list_filter = ('type',)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'city', 'is_active')
    search_fields = ('name', 'city')
    list_filter = ('category', 'city', 'is_active')