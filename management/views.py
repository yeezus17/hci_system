from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
import cloudinary.uploader

from core import settings
from .models import Service, Category, Annonce, Profile, AnnonceMedia, BuyRequest
from management.forms import AnnonceForm, HCISignupForm, BuyRequestForm, ServiceForm

def is_approved(user):
    return user.is_staff or (hasattr(user, 'profile') and user.profile.is_approved_editor)

# --- HOME & ANNONCES ---
def home(request):
    latest_annonces = Annonce.objects.all().order_by('-id')[:3]
    return render(request, 'management/home.html', {'annonces': latest_annonces})

def annonces_list(request):
    annonces = Annonce.objects.all().order_by('-id')
    # Filter out 'ACHAT' since we now have a separate BuyRequest system
    annonces = annonces.exclude(type_transaction='ACHAT')

    query = request.GET.get('q')
    transaction = request.GET.get('transaction')
    type_bien = request.GET.get('type')
    ville = request.GET.get('ville')
    max_price = request.GET.get('max_price')

    if query: annonces = annonces.filter(Q(titre__icontains=query) | Q(description__icontains=query))
    if transaction: annonces = annonces.filter(type_transaction=transaction)
    if type_bien: annonces = annonces.filter(type_bien=type_bien)
    if ville: annonces = annonces.filter(ville=ville)
    if max_price and max_price.isdigit(): annonces = annonces.filter(prix__lte=max_price)

    return render(request, 'management/annonces_list.html', {'annonces': annonces})

def annonce_detail(request, pk):
    annonce = get_object_or_404(Annonce, pk=pk)
    # Grab all associated photos/videos for this announcement
    medias = AnnonceMedia.objects.filter(annonce=annonce)
    
    context = {
        'annonce': annonce,
        'medias': medias,
    }

    return render(request, 'management/annonces_details.html', context)

@login_required
@user_passes_test(is_approved, login_url='pending_approval')
def publier_annonce(request):
    if request.method == "POST":
        form = AnnonceForm(request.POST, request.FILES)
        if form.is_valid():
            annonce = form.save(commit=False)
            annonce.auteur = request.user
            annonce.save()
            files = request.FILES.getlist('media_files')
            for f in files:
                is_video = f.content_type.startswith('video')
                resource_type = 'video' if is_video else 'image'
                upload_result = cloudinary.uploader.upload(f, resource_type=resource_type, folder='annonces/')
                AnnonceMedia.objects.create(annonce=annonce, file=upload_result['public_id'], is_video=is_video)
            messages.success(request, "Annonce publiée avec succès !")
            return redirect('home')
    else:
        form = AnnonceForm()
    return render(request, 'management/publier_annonce.html', {'form': form, 'google_maps_key': settings.GOOGLE_MAPS_KEY})

# --- BUY REQUESTS ---
@login_required
def create_buy_request(request):
    if request.method == 'POST':
        form = BuyRequestForm(request.POST)
        if form.is_valid():
            buy_request = form.save(commit=False)
            buy_request.user = request.user
            buy_request.save()
            messages.success(request, "Votre demande d'achat a été enregistrée !")
            return redirect('home')
    else:
        form = BuyRequestForm()
    return render(request, 'management/buyrequest.html', {'form': form})

@login_required
def delete_buy_request(request, pk):
    if request.method == 'POST':
        # Safely fetch the request only if it belongs to the logged-in user
        buy_request = get_object_or_404(BuyRequest, pk=pk, user=request.user)
        buy_request.delete()
        messages.success(request, "Alerte de recherche supprimée avec succès.")
    return redirect('user_profile')

# --- SERVICES ---
def services_list(request):
    service_type = request.GET.get('type', 'prestataire')
    results = Service.objects.filter(category__type=service_type, is_active=True).select_related('category', 'owner')
    
    # ... (Keep your filtering logic from before) ...
    context = {'results': results, 'service_type': service_type}
    return render(request, 'management/services_list.html', context)

@login_required
def create_service(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES)
        if form.is_valid():
            service = form.save(commit=False)
            service.owner = request.user
            service.is_active = False # Admin approval required
            service.save()
            messages.success(request, "Service soumis pour validation.")
            return redirect('services_list')
    else:
        form = ServiceForm()
    return render(request, 'management/services_form.html', {'form': form})

# --- AUTHENTICATION & PROFILE ---
@login_required
def profile_view(request):
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        # 1. Update core User details
        user.first_name = request.POST.get('first_name', user.first_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        
        # 2. Update Profile Model details
        profile.phone_number = request.POST.get('phone_number', profile.phone_number)
        profile.bio = request.POST.get('bio', profile.bio)
        if 'image' in request.FILES: 
            profile.image = request.FILES['image']
        profile.save()
        
        messages.success(request, "Profil mis à jour.")
        return redirect('user_profile')
    
    # 3. Gather active search preferences for the GET request
    saved_searches = BuyRequest.objects.filter(user=user).order_by('-id')
    
    context = {
        'profile': profile,
        'saved_searches': saved_searches,
    }
    
    return render(request, 'management/profile.html', context)

def signup_view(request):
    if request.method == 'POST':
        form = HCISignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Inscription réussie !")
            return redirect('login')
    else:
        form = HCISignupForm()
    return render(request, 'management/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'management/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

def pending_approval(request):
    return render(request, 'management/pending_approval.html')