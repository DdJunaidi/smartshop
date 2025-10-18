# backend/views_auth.py
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework import status
from .models import LoginEvent

class IssueToken(TokenObtainPairView):
    """Wrap default JWT issue and log the event."""
    def post(self, request, *args, **kwargs):
        resp = super().post(request, *args, **kwargs)
        if resp.status_code == status.HTTP_200_OK:
            # pull validated user from serializer
            try:
                ser = self.get_serializer(data=request.data)
                ser.is_valid(raise_exception=False)
                user = getattr(ser, "user", None)
            except Exception:
                user = None

            if user:
                LoginEvent.objects.create(
                    user=user,
                    ip=self._client_ip(request),
                    user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:1024],
                )
        return resp

    def _client_ip(self, request):
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
