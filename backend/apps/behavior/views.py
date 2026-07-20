from rest_framework.views import APIView
from rest_framework.response import Response

class BehaviorViewStub(APIView):
    """Behavior data is included inline in process-frame response."""
    def get(self, request):
        return Response({'message': 'Use /api/process-frame/ for behavior data.'})
