from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import Max

class User(AbstractUser):
    pass

# I need at least these models:
# categories

class Listing(models.Model):
    name = models.CharField(max_length=128)
    description = models.CharField(
        max_length=1024,
        help_text="Please provide a detailed description of the item being auctioned."
        )
    starting_bid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="The minimum amount that a bidder can offer for this item."
    )
    watchlist = models.ManyToManyField('Watchlist', related_name='listings', blank=True)
    bids = models.ManyToManyField('Bid', related_name='listing_bids', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    num_bids = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    categories = models.ManyToManyField('Category', blank=True, related_name="category_listings")
    image = models.ImageField(upload_to='listing_images/', blank=True, null=True)

    def get_winner(self):
        if not self.active:
            highest_bid = self.bids.all().aggregate(Max('amount'))['amount__max']
            if highest_bid is not None:
                return self.bids.filter(amount=highest_bid).first().user
        return None

    def __str__(self):
        return f"Listing Name: {self.name} Description: {self.description} Starting Bid: ${self.starting_bid}"
    
class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlists')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Watched by {self.user.username}"
    
class Bid(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bids')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bid_listings')
    created_at = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.listing.num_bids += 1
        self.listing.save()

    def __str__(self):
        return f"${self.amount} bid by {self.user.username} for {self.listing.name}"
    
class Comment(models.Model):
    content=models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_comments')
    listing=models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='listing_comments')
    
    def __str__(self):
        return f"Comment by {self.created_by.username} on {self.listing.name}"

class Category(models.Model):
    name = models.TextField(max_length=64)

    def __str__(self):
        return f"{self.name}"