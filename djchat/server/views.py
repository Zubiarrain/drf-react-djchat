# from django.shortcuts import render
from django.db.models import Count
from rest_framework import viewsets
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.response import Response

from .models import Server
from .schema import server_list_docs
from .serializer import ServerSerializer


# Create your views here.
@server_list_docs
class ServerListViewSet(viewsets.ViewSet):
    queryset = Server.objects.all()

    def list(self, request):
        """
        Lists servers based on specified query parameters.

        This method retrieves a list of servers based on the query parameters provided
        in the HTTP request. The method accepts several query parameters to filter and
        manipulate the list of servers.

        #### Args:
            request (Request): The HTTP request object containing query parameters.

        #### Query Parameters:
        - `category (str, optional):` Filter servers by category name.

        - `qty (int, optional):` Limit the number of servers returned.

        - `by_user (bool, optional):` Filter servers by the currently authenticated user.

        - `by_serverid (int, optional):` Filter servers by server ID.

        - `with_num_members (bool, optional):` Include the number of members for each server.

        #### Raises:
        - `AuthenticationFailed:` If the user is not authenticated and attempts to filter by user or server ID.

        - `ValidationError:` If there is an issue with the provided query parameters, such as an invalid server ID.

        #### Returns:
        `Response:` A response containing serialized server data.

        #### Example:
            Sample usage of this method:

            >>> Example usage
            >>> import requests
            >>> response = requests.get('http://example.com/api/server/?category=web&qty=10')
            >>> print(response.json())
            [
                {
                    "id": 1,
                    "name": "Web Server 1",
                    "category": "web",
                    "num_members": 5
                },
                {
                    "id": 2,
                    "name": "Web Server 2",
                    "category": "web",
                    "num_members": 3
                },
                ...
            ]

        """
        category = request.query_params.get("category")
        qty = request.query_params.get("qty")
        by_user = request.query_params.get("by_user") == "true"
        by_serverid = request.query_params.get("by_serverid")
        with_num_members = request.query_params.get("with_num_members") == "true"

        if category:
            self.queryset = self.queryset.filter(category__name=category)

        if by_user:
            if request.user.is_authenticated:
                user_id = request.user.id
                self.queryset = self.queryset.filter(member=user_id)
            raise AuthenticationFailed()

        if with_num_members:
            self.queryset = self.queryset.annotate(num_members=Count("member"))

        if by_serverid:
            if not request.user.is_authenticated:
                raise AuthenticationFailed()
            try:
                self.queryset = self.queryset.filter(id=by_serverid)
                if not self.queryset.exists():
                    raise ValidationError(
                        detail=f"Server with id {by_serverid} not found"
                    )
            except ValueError:
                raise ValidationError(detail="Server value error")

        if qty:
            self.queryset = self.queryset[: int(qty)]

        serializer = ServerSerializer(
            self.queryset, many=True, context={"num_members": with_num_members}
        )
        return Response(serializer.data)
