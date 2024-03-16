from django.utils import timezone
import decimal
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from django.db import IntegrityError
from django.db.models import Max, Count
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.core.exceptions import PermissionDenied

from .models import *
from .forms import *


def index(request):
    listings = Listing.objects.all().order_by('-created_at')
    for listing in listings:
        highest_bid = listing.bid_listings.all().aggregate(Max('amount'))['amount__max']
        listing.highest_bid = highest_bid
        listing.num_bids = listing.bid_listings.all().count()
        created_at = listing.created_at
        now = timezone.now()
    return render(request, "auctions/index.html", {
        "listings": listings,
        "now": now,
        "created_at": created_at
    })

def create_listing(request):
    if request.method == "POST":
        form = ListingForm(request.POST, request.FILES)
        new_category_name = request.POST.get('new_category')

        if form.is_valid():
            listing = form.save(commit=False)
            listing.created_by = request.user
            listing.save()

            # Handle existing categories
            existing_categories = form.cleaned_data['categories']
            listing.categories.set(existing_categories)

            # Handle new category
            new_category_name = form.cleaned_data['new_category']
            if new_category_name:
                new_category, created = Category.objects.get_or_create(name=new_category_name)
                listing.categories.add(new_category)

            listing.save()
            form.save_m2m()
            return HttpResponseRedirect(reverse('index'))
    else:
        form = ListingForm()
    return render(request, "auctions/create-listing.html", {
        "form": form
    })

def listing(request, listing_pk):
    listing = Listing.objects.get(pk=listing_pk)
    user = request.user
    bids = listing.bids.all()
    bid = bids.aggregate(Max('amount'))['amount__max']
    categories = listing.categories.all()
    
    if listing.bids.all().exists():
        highest_bid = bid
    else:
        highest_bid = listing.starting_bid - decimal.Decimal('0.01')

    initial_bid = highest_bid + decimal.Decimal('0.01') # add one cent to the highest bid to get the minimum valid value
    created_at = listing.created_at
    bid_form = BidForm(listing=listing, initial={'bid_amount': initial_bid})
    comment_form = CommentForm()

    if user.is_authenticated:
        watchlist, created = Watchlist.objects.get_or_create(user=user)
        in_watchlist = watchlist.listings.filter(pk=listing.pk).exists()
        is_creator = listing.created_by == user
        is_highest_bid_yours = listing.bids.filter(user=user, amount=highest_bid).exists()
        print("Comments:")
        print(listing.listing_comments.all)
        context = {
            "listing": listing,
            "created_at": created_at,
            "now": timezone.now(),
            "in_watchlist": in_watchlist,
            "bid_form": bid_form,
            "comment_form": comment_form,
            "bids": bids,
            "bid": bid,
            "highest_bid": highest_bid,
            "is_creator": is_creator,
            "yours": is_highest_bid_yours,
            "categories": categories
            }
    else:
        context = {
            "listing": listing,
            "created_at": created_at,
            "now": timezone.now(),
            "bid": bid,
            "highest_bid": highest_bid
            }

    return render(request, "auctions/listing.html", context)

def my_listings(request):
    user = request.user
    my_listings = user.listings.all().order_by('-created_at')
    for listing in my_listings:
        highest_bid = listing.bid_listings.all().aggregate(Max('amount'))['amount__max']
        listing.highest_bid = highest_bid
        listing.num_bids = listing.bid_listings.all().count()
    return render(request, "auctions/my-listings.html", {
        "my_listings": my_listings
    })

@login_required
def close_auction(request, listing_pk):
    listing = get_object_or_404(Listing, pk=listing_pk)
    if listing.created_by == request.user:
        if request.method == "POST":
            listing.active = False
            listing.save()
            return redirect('listing', listing_pk=listing.pk)
        return redirect('listing', listing_pk=listing.pk)
    else:
        raise PermissionDenied

@login_required
def delete_listing(request, listing_pk):
    listing = get_object_or_404(Listing, pk=listing_pk)
    if listing.created_by == request.user:
        listing.delete()
        return redirect('my_listings')
    else:
        raise PermissionDenied

def add_to_watchlist(request, listing_pk):
    listing = get_object_or_404(Listing, pk=listing_pk)
    user = request.user
    if user.is_authenticated:
        watchlist, created = Watchlist.objects.get_or_create(user=user)
        watchlist.listings.add(listing)
    return redirect('listing', listing_pk=listing_pk)

def remove_from_watchlist(request, listing_pk):
    listing = get_object_or_404(Listing, pk=listing_pk)
    user = request.user

    if user.is_authenticated:
        watchlist = Watchlist.objects.get(user=user)
        watchlist.listings.remove(listing)

    referer = request.GET.get('referer')
    if referer == 'listing':
        return redirect('listing', listing_pk=listing.pk)
    elif referer == 'watchlist':
        return redirect('watchlist')
    else:
        # Handle invalid referer value
        return redirect('index')

def watchlist(request):
    if request.user.is_authenticated:
        watchlist = Watchlist.objects.get(user=request.user)
        listings = watchlist.listings.all().order_by('-created_at')
        for listing in listings:
            highest_bid = listing.bid_listings.all().aggregate(Max('amount'))['amount__max'] or listing.starting_bid
            listing.highest_bid = highest_bid
            listing.num_bids = listing.bid_listings.all().count()
            listing.yours = listing.bids.filter(user=request.user, amount=highest_bid).exists()
    else:
        listings = []
    return render(request, "auctions/watchlist.html", {
        'listings': listings
        })

def place_bid(request, listing_pk):
    listing = get_object_or_404(Listing, pk=listing_pk)
    bid = listing.bids.all().aggregate(Max('amount'))['amount__max']

    if listing.bids.all().exists():
        highest_bid = bid
    else:
        highest_bid = listing.starting_bid - decimal.Decimal('0.01')

    user = request.user
    created_at = listing.created_at
    now = timezone.now()

    initial_bid = highest_bid + decimal.Decimal('0.01')  # add one cent to the highest bid to get the minimum valid value

    if request.method == 'POST':
        form = BidForm(request.POST, listing=listing)
        if form.is_valid():
            bid_amount = form.cleaned_data['bid_amount']
            bid = Bid.objects.create(user=user, listing=listing, amount=bid_amount)
            listing.bids.add(bid)
            add_to_watchlist(request, listing_pk)
            return redirect('listing', listing_pk=listing.pk)
    else:
        form = BidForm(listing=listing, initial={'bid_amount': initial_bid})

    # If the form is invalid, pre-populate the bid_amount field with the minimum valid value
    if 'bid_amount' in form.errors:
        form.initial['bid_amount'] = initial_bid

    context = {'listing': listing, 'form': form, 'bid': bid, 'highest_bid': highest_bid, 'error_message': 'Your bid must be higher than the current highest bid or equal to the starting bid.', 'now': now, 'created_at': created_at}
    return render(request, 'auctions/listing.html', context)

@login_required
def leave_comment(request, listing_pk):
    listing = get_object_or_404(Listing, pk=listing_pk)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.created_by = request.user
            comment.listing = listing
            comment.save()
            return redirect("listing", listing_pk=listing_pk)
    else:
        form = CommentForm()
    return render(request, "auctions/listing.html", {
        "listing": listing,
        "comment_form": form
    })

def categories(request):
    categories = Category.objects.all().annotate(listing_count=Count('category_listings'))
    return render(request, "auctions/categories.html", {
        "categories": categories
    })

def category(request, category_pk):
    category = get_object_or_404(Category, pk=category_pk)
    listings = category.category_listings.all().order_by('-created_at')
    return render(request, "auctions/category.html", {
        "listings": listings
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
