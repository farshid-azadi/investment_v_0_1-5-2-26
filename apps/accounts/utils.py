# apps/accounts/utils.py
import string
import random
from collections import deque
from decimal import Decimal
from django.db import transaction

from apps.core.models import LevelCommissionSetting
from apps.wallet.models import Transaction


@transaction.atomic
def distribute_level_commission(buyer, plan_price):
    settings = LevelCommissionSetting.objects.filter(is_active=True).order_by("level")

    current_user = buyer.referrer
    level = 1

    for setting in settings:
        if not current_user:
            break

        # ❌ Anti‑Ponzi: بالاسری پلن فعال ندارد
        if not hasattr(current_user, "active_plan") or not current_user.active_plan.is_active:
            current_user = current_user.referrer
            level += 1
            continue

        if level != setting.level:
            current_user = current_user.referrer
            level += 1
            continue

        commission = Decimal(plan_price) * (setting.percent / Decimal("100"))

        wallet = current_user.wallet

        wallet.balance += commission
        wallet.save(update_fields=["balance"])

        Transaction.objects.create(
            wallet=wallet,
            amount=commission,
            tx_type="LEVEL_COMMISSION",
            meta={
                "from_user_id": buyer.id,
                "level": level,
                "percent": float(setting.percent),
            }
        )

        # history
        LevelCommissionHistory.objects.create(
            earner=current_user,
            from_user=buyer,
            level=level,
            amount=commission
        )

        current_user = current_user.referrer
        level += 1


def generate_ref_code():
    code_length = 8
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(code_length))
def find_binary_parent(start_user):
    """
    پیدا کردن اولین جای خالی در درخت باینری
    الگوریتم BFS
    """

    queue = deque([start_user])

    while queue:
        current = queue.popleft()

        left_child = current.binary_children.filter(binary_position="left").first()
        right_child = current.binary_children.filter(binary_position="right").first()

        if not left_child:
            return current, "left"

        if not right_child:
            return current, "right"

        queue.append(left_child)
        queue.append(right_child)

    return None, None

@transaction.atomic
def propagate_volume(user, amount):
    """
    انتقال حجم فروش به بالاسری‌های باینری
    فقط به کاربرانی که پلن فعال دارند
    """

    current = user

    while current.binary_parent:
        parent = current.binary_parent

        # ✅ کنترل حیاتی: فقط کاربر Active حجم می‌گیرد
        if not hasattr(parent, "active_plan") or not parent.active_plan.is_active:
            current = parent
            continue

        if current.binary_position == "left":
            parent.left_volume += Decimal(amount)
        else:
            parent.right_volume += Decimal(amount)

        parent.save(update_fields=["left_volume", "right_volume"])
        current = parent