from rest_framework.response import Response
from rest_framework.views import APIView

from seminare.organizer.api.auth import OIDCAuthentication
from seminare.users.models import User


class UserPushAPIView(APIView):
    authentication_classes = [OIDCAuthentication]
    permission_classes = []

    def post(self, request, *args, **kwargs):
        data = request.data

        user = User.objects.filter(trojsten_id=data.get("id")).first()

        if user is None:
            return Response(status=404)

        user.email = data.get("email")
        user.username = data.get("username")
        user.first_name = data.get("first_name")
        user.last_name = data.get("last_name")
        user.update_school_info(data.get("current_school_record"))

        user.save()

        return Response(status=200)
