from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', ]

    ROLE_CHOICES = [
        ('anonim', 'Anonim'),
        ('user', 'User'),
        ('moderator', 'Moderator'),
        ('admin', 'Admin'),
    ]

    email = models.EmailField(
        _('email address'),
        help_text='Введите почту',
        unique=True
    )
    bio = models.CharField(
        max_length=500,
        verbose_name='Биография',
        help_text='Расскажите о себе',
        blank=True
    )
    role = models.CharField(
        max_length=250,
        verbose_name='Роль пользователя',
        help_text='Укажите роль',
        choices=ROLE_CHOICES,
        default='user'
    )

    def create_token(self, user):
        token = default_token_generator.make_token(user)
        send_mail(
            'confirmation_code',
            token,
            settings.EMAIL_FROM_ADMIN,
            [user.email],
            fail_silently=False,
        )

    def is_moderator(self):
        if self.role == 'moderator':
            return True

    def is_admin(self):
        if self.role == 'admin':
            return True

    class Meta:
        ordering = ['-id']


class Categories(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name='Наименование категории',
        help_text='Укажите категорию')
    slug = models.SlugField(unique=True, max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-id']


class Genres(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name='Жанр произведения',
        help_text='Укажите жанр'
    )
    slug = models.SlugField(unique=True, max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-id']


class Titles(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name='Название произведения',
        help_text='Укажите произведение'
    )
    year = models.PositiveSmallIntegerField(
        verbose_name='Год выхода произведения',
        help_text='Укажите год публикации произведения'
    )
    description = models.TextField(
        verbose_name='Описание произведения',
        help_text='Укажите описание',
        blank=True)
    genre = models.ManyToManyField(
        Genres,
        blank=True,
        verbose_name='Жанр',
        help_text='Выберите жанр',
        related_name='titles'
    )
    category = models.ForeignKey(
        Categories,
        on_delete=models.SET_NULL,
        verbose_name='Категория',
        help_text='Выберите категорию',
        related_name='titles',
        null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-id']


class Review(models.Model):
    score = models.IntegerField(
        verbose_name='Оценка произведения',
        help_text='Оцените произведение',
        validators=(
            MinValueValidator(1, message='Укажите число не меньше 1'),
            MaxValueValidator(10, message='Укажите число не больше 10'),
        )
    )
    text = models.TextField(
        verbose_name='Текст отзыва',
        help_text='Добавьте текст отзыва',
        blank=True,
        null=True
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата отзыва',
        help_text='Укажите дату отзыва',
        auto_now_add=True,
        db_index=True,
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        help_text='Выберите автора',
        related_name='reviews',
        on_delete=models.CASCADE,
    )
    title = models.ForeignKey(
        Titles,
        related_name='reviews',
        verbose_name='Произведение',
        help_text='Укажите произведение',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'Отзыв'
        unique_together = ['author', 'title']
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text


class Comment(models.Model):
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        help_text='Укажите автора',
        on_delete=models.CASCADE,
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Добавьте комментарий'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации комментария',
        help_text='Укажите дату публикации комментария',
        auto_now_add=True,
    )
    review = models.ForeignKey(
        Review,
        related_name='comments',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name='Отзыв',
        help_text='Укажите отзыв'
    )

    class Meta:
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text
