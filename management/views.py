from urllib import request

from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Q
from .models import Service, Category
from management.forms import AnnonceForm, HCISignupForm
from .models import Annonce, Profile
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render, get_object_or_404 
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test




def is_approved(user):
    return user.is_staff or (hasattr(user, 'profile') and user.profile.is_approved_editor)

def home(request):
    latest_annonces = Annonce.objects.all().order_by('-id')[:3]
    # Change 'home.html' to 'management/home.html'
    return render(request, 'management/home.html', {'annonces': latest_annonces})

def annonces_list(request):
    # Start with all ads
    annonces = Annonce.objects.all().order_by('-id')

    # 1. Search
    query = request.GET.get('q')
    if query:
        annonces = annonces.filter(Q(titre__icontains=query) | Q(description__icontains=query))

    # 2. Transaction (Achat/Vente/Louer)
    transaction = request.GET.get('transaction')
    if transaction:
        annonces = annonces.filter(type_transaction=transaction)

    # 3. Property Type (Villa/Appart/etc)
    type_bien = request.GET.get('type')
    if type_bien:
        annonces = annonces.filter(type_bien=type_bien)

    # 4. City
    ville = request.GET.get('ville')
    if ville:
        annonces = annonces.filter(ville=ville)

    # 5. Price
    max_price = request.GET.get('max_price')
    if max_price and max_price.isdigit():
        annonces = annonces.filter(prix__lte=max_price)

    return render(request, 'management/annonces_list.html', {'annonces': annonces})

@login_required
@user_passes_test(is_approved, login_url='pending_approval')
def publier_annonce(request):
    if request.method == "POST":
        # Ensure request.FILES is passed to catch the images/videos
        form = AnnonceForm(request.POST, request.FILES)
        
        if form.is_valid():
            # 1. Save the main data (title, price, etc.)
            annonce = form.save(commit=False)
            annonce.auteur = request.user
            annonce.save()

            # 2. Retrieve the list of multiple files from the 'media_files' field
            files = request.FILES.getlist('media_files')

            # 3. Loop through files and create AnnonceMedia objects
            for f in files:
                # Check if file is a video by inspecting its MIME type
                is_video = f.content_type.startswith('video')
                
                # Import AnnonceMedia locally if not at top of file
                from .models import AnnonceMedia
                AnnonceMedia.objects.create(
                    annonce=annonce,
                    file=f,
                    is_video=is_video
                )

            messages.success(request, "Votre annonce a été publiée avec succès !")
            return redirect('home')
        else:
            # Enhanced error logging to see exactly why validation failed
            messages.error(request, "Erreur lors de la validation. Vérifiez les champs.")
    else:
        form = AnnonceForm()
        
    return render(request, 'management/publier_annonce.html', {'form': form})


def services_list(request):
    # Default to prestataire but allow the user to toggle
    service_type = request.GET.get('type', 'prestataire')
    
    query = request.GET.get('q')
    category_id = request.GET.get('category')
    city = request.GET.get('city')

    # 1. Base Query: Use select_related to join Category in one hit
    results = Service.objects.filter(
        category__type=service_type, 
        is_active=True
    ).select_related('category', 'owner')

    # 2. Enhanced Search: Look in name AND description
    if query:
        results = results.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )
    
    # 3. Direct Filters
    if category_id:
        results = results.filter(category_id=category_id)
        
    if city:
        results = results.filter(city__iexact=city)

    # 4. Marketplace Ordering: Boosted first (Fusée Orange), then Newest
    results = results.order_by('-is_boosted', '-date_created')

    # 5. Filter sidebar data
    filter_categories = Category.objects.filter(type=service_type)
    # Get all unique cities that actually have services to populate a dropdown
    available_cities = Service.objects.filter(is_active=True).values_list('city', flat=True).distinct()

    context = {
        'results': results,
        'service_type': service_type,
        'filter_categories': filter_categories,
        'available_cities': available_cities,
        'current_city': city,
        'current_query': query,
        'current_category': category_id,
    }
    
    return render(request, 'management/services_list.html', context)

@login_required(login_url='login') # Make sure 'login' matches your login URL name
def create_service(request):
    if request.method == 'POST':
        # Extract data directly from the HTML form
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        city = request.POST.get('city')
        logo = request.FILES.get('logo') # Use request.FILES for images

        # Basic validation to ensure required fields aren't empty
        if name and category_id and description and city:
            try:
                category = Category.objects.get(id=category_id)
                
                # Create the service in the database
                Service.objects.create(
                    owner=request.user, # Automatically link to the logged-in user
                    name=name,
                    category=category,
                    description=description,
                    city=city,
                    logo=logo,
                    is_active=False, # Force false so admin has to approve it
                    is_boosted=False
                )
                
                # Send a success message to trigger SweetAlert
                messages.success(request, "Votre service a été soumis avec succès ! Il sera visible après validation par notre équipe.")
                return redirect('services_list') # Adjust to your actual list view name
                
            except Category.DoesNotExist:
                messages.error(request, "Catégorie invalide.")
        else:
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")

    # If GET request, just show the form with available categories
    categories = Category.objects.all().order_by('type', 'name')
    context = {
        'categories': categories
    }
    categories = Category.objects.all().order_by('name')
    return render(request, 'management/services_form.html', context)


def annonce_detail(request, pk):
    annonce = get_object_or_404(Annonce, pk=pk)
    return render(request, 'management/annonces_details.html', {'annonce': annonce})

@login_required
def profile_view(request):
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.email = request.POST.get('email', user.email)
        user.save()

        profile.phone_number = request.POST.get('phone_number', profile.phone_number)
        profile.bio = request.POST.get('bio', profile.bio)
        
        if 'image' in request.FILES:
            profile.image = request.FILES['image']
        
        profile.save()
        messages.success(request, "Vos modifications ont été enregistrées.")
        return redirect('user_profile')

    # --- CALCULATION LOGIC ---
    # Define fields to check
    fields_to_check = [
        user.first_name,
        user.email,
        profile.phone_number,
        profile.bio,
        profile.image
    ]
    
    # Calculate percentage
    filled_fields = [f for f in fields_to_check if f]
    completion_percentage = int((len(filled_fields) / len(fields_to_check)) * 100)

    # Get user's announcement count for the dashboard stats
    annonce_count = Annonce.objects.filter(auteur=user).count()

    context = {
        'profile': profile,
        'completion_percentage': completion_percentage,
        'annonce_count': annonce_count
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
            # Loop through specific field errors
            for field, errors in form.errors.items():
                for error in errors:
                    # This makes the message clear: e.g., "Email: Cet utilisateur existe déjà."
                    messages.error(request, f"{field.replace('_', ' ').capitalize()}: {error}")
    else:
        form = HCISignupForm()
    
    return render(request, 'management/signup.html', {'form': form})
def login_view(request): 
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
        # If login fails, form with errors will be passed to render
    else:
        form = AuthenticationForm()
        
    return render(request, 'management/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

def pending_approval(request):
    return render(request, 'management/pending_approval.html')
