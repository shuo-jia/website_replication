from django.shortcuts import render
from .forms import RegisterUserForm


# Create your views here.
def register(request):
    is_valid = False
    recommit = False
    if request.method == "POST":
        form = RegisterUserForm(request.POST)
        recommit = True
        if form.is_valid():
            form.save()
            is_valid = True
    else:
        form = RegisterUserForm()
    return render(request, "user/register.html", {
        'form': form,
        'register_success': is_valid,
        'recommit': recommit,
    })
