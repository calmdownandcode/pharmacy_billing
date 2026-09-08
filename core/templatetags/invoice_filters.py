from django import template
from num2words import num2words
from decimal import Decimal

register = template.Library()

@register.filter(name='amt_in_words')
def amt_in_words(value):
    try:
        # Convert values safely into an integer format
        amount = int(Decimal(str(value)))
        
        # Generate words using Indian numbering nomenclature format (Lakhs/Crores)
        words = num2words(amount, lang='en_IN').title()
        
        return f"{words} Rupees Only"
    except (TypeError, ValueError, KeyError):
        return ""
