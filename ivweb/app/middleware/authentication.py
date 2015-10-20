from ivetl.models import User, Anonymous_User


class AuthenticationMiddleware(object):

    def process_view(self, request, view_func, view_args, view_kwargs):
        user_id = request.session.get('user_id')
        user = None

        if user_id:
            try:
                user = User.objects.get(user_id=user_id)
            except User.DoesNotExist:
                pass

        if not user:
            user = Anonymous_User()

        request.user = user
