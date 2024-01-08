from django.core import signing
from django.http import HttpResponseRedirect
from django.urls import reverse
class ForceChangePasswordMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated:
            user = request.user
            if user.force_change_pass:
                if request.path != "/accounts/resetpassword/":
                    return HttpResponseRedirect(reverse('accounts:reset-password'))

class AddCustomCSRFToRequestMiddleware(object):
    def __init__(self, get_response):
        # One-time configuration and initialization.
        self.get_response = get_response

    def __call__(self, request):
        # Code to be executed for each request before the view (and later
        # middleware) are called.

        if request.method == "POST":
            # Make it editabble
            if not request.POST._mutable:
                request.POST._mutable = True

            # Get the default CSRF Field value (If any)
            csrf_token = request.POST.get("csrfmiddlewaretoken", "")

            # If there is no csrfmiddlewaretoken in the POST
            # then look for our custom CSRF Field
            if csrf_token == "":
                # Create the field name
                csrf_field = signing.dumps("csrfmiddlewaretoken").partition(":")[0]

                # Get the value
                request_csrf_token = request.POST.get(csrf_field, "")

                # Set it as csrfmiddlewaretoken so Django can look for it
                request.POST["csrfmiddlewaretoken"] = request_csrf_token

                # Make sure it's not editable before passing the
                # request to the next chain
                request.POST._mutable = False

        response = self.get_response(request)

        # Code to be executed for each request/response after the view is
        # called.

        return response
