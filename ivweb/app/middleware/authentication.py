from ivetl.models import User, AnonymousUser


class AuthenticationMiddleware(object):

    def process_view(self, request, view_func, view_args, view_kwargs):
        email = request.session.get('user_email')
        user = None

        if email:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                pass

        if not user:
            user = AnonymousUser()

        request.user = user
