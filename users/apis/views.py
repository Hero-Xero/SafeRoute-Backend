from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from users.apis.serializers import RefreshTokenSerializer


class RefreshTokenAPIView(APIView):
    """
    Refresh access token view
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
