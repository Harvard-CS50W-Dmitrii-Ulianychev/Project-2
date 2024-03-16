import decimal
from django import forms
from django.db.models import Max
from .models import Listing, Comment, Category

class ListingForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'size': 5}),
    )
    new_category = forms.CharField(required=False, label="New Category")

    class Meta:
        model = Listing
        fields = ('name', 'description', 'starting_bid', 'categories', 'new_category', 'image')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categories'].queryset = Category.objects.all()

class BidForm(forms.Form):
    bid_amount = forms.DecimalField(label='Place a bid', decimal_places=2, min_value=0.01, required=True)

    def __init__(self, *args, **kwargs):
        self.listing = kwargs.pop('listing', None)
        super().__init__(*args, **kwargs)

    def clean_bid_amount(self):
        bid_amount = self.cleaned_data['bid_amount']

        starting_minus = self.listing.starting_bid - decimal.Decimal('0.01')
        
        highest_bid = self.listing.bids.all().aggregate(Max('amount'))['amount__max'] or starting_minus

        if bid_amount <= highest_bid:
            raise forms.ValidationError('Your bid must be higher than the current highest bid or equal to the starting bid.')

        return bid_amount

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('content',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].widget.attrs.update({'class': 'custom-content-field'})