from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from netbox.api import ContentTypeField, SerializedPKRelatedField, ValidatedModelSerializer
from users.models import ObjectPermission, Token
from .nested_serializers import *


__all__ = (
    'GroupSerializer',
    'ObjectPermissionSerializer',
    'TokenSerializer',
    'UserSerializer',
)


class UserSerializer(ValidatedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='users-api:user-detail')
    groups = SerializedPKRelatedField(
        queryset=Group.objects.all(),
        serializer=NestedGroupSerializer,
        required=False,
        many=True
    )

    class Meta:
        model = User
        fields = (
            'id', 'url', 'display', 'username', 'password', 'first_name', 'last_name', 'email', 'is_staff', 'is_active',
            'date_joined', 'groups',
        )
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        """
        Extract the password from validated data and set it separately to ensure proper hash generation.
        """
        password = validated_data.pop('password')
        user = super().create(validated_data)
        user.set_password(password)
        user.save()

        return user


class GroupSerializer(ValidatedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='users-api:group-detail')
    user_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Group
        fields = ('id', 'url', 'display', 'name', 'user_count')


class TokenSerializer(ValidatedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='users-api:token-detail')
    key = serializers.CharField(min_length=40, max_length=40, allow_blank=True, required=False)
    user = NestedUserSerializer()

    class Meta:
        model = Token
        fields = ('id', 'url', 'display', 'user', 'created', 'expires', 'key', 'write_enabled', 'description')

    def to_internal_value(self, data):
        if 'key' not in data:
            data['key'] = Token.generate_key()
        return super().to_internal_value(data)


class ObjectPermissionSerializer(ValidatedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='users-api:objectpermission-detail')
    object_types = ContentTypeField(
        queryset=ContentType.objects.all(),
        many=True
    )
    groups = SerializedPKRelatedField(
        queryset=Group.objects.all(),
        serializer=NestedGroupSerializer,
        required=False,
        many=True
    )
    users = SerializedPKRelatedField(
        queryset=User.objects.all(),
        serializer=NestedUserSerializer,
        required=False,
        many=True
    )

    class Meta:
        model = ObjectPermission
        fields = (
            'id', 'url', 'display', 'name', 'description', 'enabled', 'object_types', 'groups', 'users', 'actions',
            'constraints',
        )
