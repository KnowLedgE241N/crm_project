from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from accounts.utils import is_volunteer


@login_required
def post_login_redirect(request):
    """
    Decide where users land after login based on role.
    """
    if is_volunteer(request.user):
        return redirect("forms_page")   # /forms/

    # everyone else
    return redirect("dashboard")
