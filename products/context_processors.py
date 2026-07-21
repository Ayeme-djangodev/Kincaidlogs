from .models import Category


def categories(request):
    return {
        "navbar_categories": Category.objects.all()
    }