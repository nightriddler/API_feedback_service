from django.contrib.auth.tokens import default_token_generator
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .filters import TitleFilter
from .models import Categories, Genres, Review, Titles, User
from .permissions import IsAdminUser, IsOwnerOrModerator, ReadOnly
from .serializers import (AuthTokenSerializer, AuthUserSerializer,
                          CategorySerializers, CommentSerializer,
                          GenresSerializers, ReviewSerializer,
                          TitlesCreateSerializer, TitlesReadSerializer,
                          UsersSerializer)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def auth_token(request):
    serializer = AuthTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email']
    user = get_object_or_404(User, email=email)

    confirmation_code = serializer.validated_data['confirmation_code']

    if default_token_generator.check_token(user, confirmation_code):
        refresh = RefreshToken.for_user(user)
        return Response(
            {'token': str(refresh.access_token)},
            status=status.HTTP_200_OK
        )
    return Response({'Incorrect'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def auth_email(request):
    serializer = AuthUserSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email']
    username = email[:email.index('@')]
    password = User.objects.make_random_password()

    user = User.objects.create_user(
        username=username,
        password=password,
        email=email
    )
    user.create_token(user)
    return Response({'email': email}, status=status.HTTP_200_OK)


class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UsersSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, ]
    filterset_fields = ['username']
    lookup_field = 'username'

    @action(
        methods=['GET'],
        permission_classes=[permissions.IsAuthenticated],
        detail=False
    )
    def me(self, request):
        serializer = self.get_serializer_class()
        data = serializer(request.user).data
        return Response(data, status=status.HTTP_200_OK)

    @action(
        permission_classes=[permissions.IsAuthenticated],
        detail=False
    )
    @me.mapping.patch
    def me_patch(self, request):
        serializer = UsersSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(role=request.user.role)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CRUDViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    pass


class CategoriesViewSet(CRUDViewSet):
    queryset = Categories.objects.all()
    serializer_class = CategorySerializers
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['name']
    search_fields = ['name', ]
    lookup_field = 'slug'
    permission_classes = [ReadOnly | IsAdminUser]


class GenresViewSet(CRUDViewSet):
    queryset = Genres.objects.all()
    serializer_class = GenresSerializers
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['name']
    search_fields = ['name', ]
    lookup_field = 'slug'
    permission_classes = [ReadOnly | IsAdminUser]


class TitlesViewSet(viewsets.ModelViewSet):
    queryset = Titles.objects.annotate(
        rating=Avg('reviews__score')).order_by('name')
    filter_backends = [DjangoFilterBackend]
    filterset_class = TitleFilter
    permission_classes = [ReadOnly | IsAdminUser]

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PATCH']:
            return TitlesCreateSerializer
        return TitlesReadSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsOwnerOrModerator]

    def perform_create(self, serializer):
        title = get_object_or_404(Titles, pk=self.kwargs.get('title_id'))
        serializer.save(author=self.request.user, title=title)

    def get_queryset(self):
        title = get_object_or_404(Titles, pk=self.kwargs.get('title_id'))
        return title.reviews.all()


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsOwnerOrModerator]

    def perform_create(self, serializer):
        review = get_object_or_404(
            Review.objects.select_related('title'),
            title__id=self.kwargs.get('title_id'),
            pk=self.kwargs.get('review_id')
        )
        return serializer.save(author=self.request.user, review=review)

    def get_queryset(self):
        review = get_object_or_404(
            Review.objects.select_related('title'),
            title__id=self.kwargs.get('title_id'),
            pk=self.kwargs.get('review_id')
        )
        return review.comments.all()
