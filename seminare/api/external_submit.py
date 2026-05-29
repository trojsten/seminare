from functools import cached_property
from typing import Any

from django.core import signing
from rest_framework import mixins, serializers, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from seminare.api.auth import (
    ExternalSubmitAuthentication,
    ExternalSubmitUserAuthentication,
)
from seminare.rules import RuleEngine
from seminare.submits.models import ExternalSubmit
from seminare.users.models import User


class ExternalSubmitAPITokenExchangeView(APIView):
    authentication_classes = [ExternalSubmitAuthentication]
    permission_classes = []

    def post(self, request, token: str):
        problem = request.auth
        try:
            data = signing.loads(token, max_age=10)

            if data.get("type") != "exchange-token":
                raise Exception()

            user = User.objects.get(id=data["user_id"])

            if data["problem_id"] != problem.id:
                raise Exception()

        except (signing.BadSignature, Exception):
            return Response({"error": "Invalid token."}, status=401)

        return Response(
            {
                "ok": True,
                "user": {
                    "id": user.id,
                    "name": user.get_full_name(),
                    "username": user.username,
                    "avatar": user.avatar_url,
                },
                "problem": {
                    "points": problem.external_points,
                    "problem_set": {
                        "start": problem.problem_set.start_date,
                        "end": problem.problem_set.end_date,
                    },
                },
            }
        )


class ExternalSubmitSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalSubmit
        fields = ["id", "score", "external_data"]

    def validate(self, attrs):
        problem = self.context["problem"]
        enrollment = self.context["enrollment"]

        if self.instance:
            assert isinstance(self.instance, ExternalSubmit)
            self.instance.problem = problem
            self.instance.enrollment = enrollment
            self.instance.full_clean()
        else:
            ExternalSubmit(**attrs, problem=problem, enrollment=enrollment).full_clean()
        attrs["enrollment"] = enrollment
        return attrs


class ExternalSubmitAPISubmitViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    authentication_classes = [ExternalSubmitUserAuthentication]
    permission_classes = []

    serializer_class = ExternalSubmitSerializer
    lookup_field = "id"

    @cached_property
    def enrollment(self):
        if not self.request.auth:
            return None

        rule_engine: RuleEngine = self.request.auth.problem_set.get_rule_engine()

        return rule_engine.get_enrollment(self.request.user, create=True)

    def get_queryset(self):
        return ExternalSubmit.objects.filter(
            problem=self.request.auth, enrollment__user=self.request.user
        )

    def perform_create(self, serializer):
        serializer.save(problem=self.request.auth, enrollment=self.enrollment)

    def get_serializer_context(self) -> dict[str, Any]:
        ctx = super().get_serializer_context()

        ctx["problem"] = self.request.auth
        ctx["enrollment"] = self.enrollment

        return ctx
