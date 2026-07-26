from .models import Wallet


def wallet_balance(request):
    if request.user.is_authenticated:
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        return {"navbar_wallet": wallet}
    return {}
