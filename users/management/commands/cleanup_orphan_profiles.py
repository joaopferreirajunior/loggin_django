from django.core.management.base import BaseCommand
from users.models import Profile
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Remove perfis órfãos (profiles sem usuário associado)'

    def handle(self, *args, **options):
        # Encontrar profiles cujo user_id não existe mais na tabela de usuários
        orphan_profiles = Profile.objects.exclude(
            user_id__in=User.objects.values_list('id', flat=True)
        )
        
        count = orphan_profiles.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('✓ Nenhum perfil órfão encontrado.')
            )
            return
        
        self.stdout.write(
            self.style.WARNING(f'Encontrados {count} perfis órfãos:')
        )
        
        for profile in orphan_profiles:
            self.stdout.write(
                f'  - Profile ID: {profile.id}, User ID: {profile.user_id}, CPF: {profile.cpf}'
            )
        
        # Perguntar confirmação
        confirm = input('\nDeseja remover estes perfis órfãos? (s/n): ')
        
        if confirm.lower() == 's':
            orphan_profiles.delete()
            self.stdout.write(
                self.style.SUCCESS(f'✓ {count} perfis órfãos removidos com sucesso!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Operação cancelada.')
            )
