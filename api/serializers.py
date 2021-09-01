from rest_framework import serializers, validators
from rest_framework.generics import get_object_or_404
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Categories, Comment, Genres, Review, Titles, User


class AuthTokenSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    confirmation_code = serializers.CharField()

    class Meta:
        fields = ('email', 'confirmation_code')
        model = User


class AuthUserSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('email',)
        model = User


class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'first_name',
            'last_name',
            'username',
            'bio',
            'email',
            'role'
        )
        model = User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        data['token'] = str(refresh.access_token)
        return {'token': data['token']}


class CategorySerializers(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = ('name', 'slug')


class GenresSerializers(serializers.ModelSerializer):
    class Meta:
        model = Genres
        fields = ('name', 'slug')


class DefaultTitleSerializer:
    requires_context = True

    def __call__(self, serializer_field):
        title_id = serializer_field.context.get('view').kwargs.get('title_id')
        title = get_object_or_404(Titles, id=title_id)
        return title


class TitlesReadSerializer(serializers.ModelSerializer):
    category = CategorySerializers(read_only=True)
    genre = GenresSerializers(many=True, read_only=True)
    rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Titles
        fields = ('__all__')


class TitlesCreateSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Categories.objects.all()
    )
    genre = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Genres.objects.all(),
        many=True
    )

    class Meta:
        model = Titles
        fields = ('__all__')


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        queryset=Review.objects.all(),
        default=serializers.CurrentUserDefault()
    )
    title = serializers.HiddenField(
        default=DefaultTitleSerializer()
    )

    class Meta:
        fields = '__all__'
        model = Review
        validators = [
            validators.UniqueTogetherValidator(
                queryset=Review.objects.all(),
                fields=['author', 'title'],
                message='You have already reviewed this title.'
            )
        ]


class CommentSerializer(serializers.ModelSerializer):
    text = serializers.CharField()
    author = serializers.SlugRelatedField(
        slug_field='username',
        queryset=Comment.objects.all(),
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        fields = ('id', 'text', 'author', 'pub_date')
        model = Comment
