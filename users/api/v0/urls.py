from django.urls import path
from .views import upload_profile_image, delete_profile_image, get_user_profile

urlpatterns = [
    # Gerenciamento de imagem de perfil
    path("profile/", get_user_profile, name="get_user_profile"),                    # GET - dados do usuário
    path("profile/image/", upload_profile_image, name="upload_profile_image"),      # POST - upload imagem
    path("profile/image/", delete_profile_image, name="delete_profile_image"),      # DELETE - remove imagem
]