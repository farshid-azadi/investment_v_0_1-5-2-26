# apps/accounts/templatetags/binary_tags.py
from django import template
from decimal import Decimal

register = template.Library()

@register.simple_tag
def volume_percentage(left_volume, right_volume, side):
    """
    محاسبه درصد حجم برای نمایش Progress Bar باینری
    
    Args:
        left_volume: حجم سمت چپ (Decimal یا int)
        right_volume: حجم سمت راست (Decimal یا int)
        side: 'left' یا 'right'
    
    Returns:
        عدد صحیح درصد (0-100)
    """
    # تبدیل به Decimal برای محاسبات دقیق
    left = Decimal(str(left_volume)) if left_volume else Decimal('0')
    right = Decimal(str(right_volume)) if right_volume else Decimal('0')
    
    total = left + right
    
    # اگر هر دو صفر باشن، 50-50 نمایش بده
    if total == 0:
        return 50
    
    # محاسبه درصد بر اساس سمت
    if side == 'left':
        percentage = (left / total) * 100
    else:
        percentage = (right / total) * 100
    
    return int(percentage)


@register.simple_tag
def format_volume(volume):
    """
    فرمت‌دهی حجم با جداکننده هزارگان
    مثال: 15000 -> 15,000
    """
    if not volume:
        return "0"
    return f"{int(volume):,}"
