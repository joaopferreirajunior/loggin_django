from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from users.models import Profile
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Cria os roles de usuários e suas permissões'

    def handle(self, *args, **options):
        self.stdout.write('Criando roles de usuários e permissões...')
        
        # Criar ou obter content types
        user_content_type = ContentType.objects.get_for_model(User)
        profile_content_type = ContentType.objects.get_for_model(Profile)
        
        # Criar permissões customizadas
        permissions_data = [
            # Permissões de sistema
            ('can_manage_system', 'Can manage system settings', user_content_type),
            ('can_view_all_users', 'Can view all users', user_content_type),
            ('can_delete_any_user', 'Can delete any user', user_content_type),
            ('can_access_admin_panel', 'Can access admin panel', user_content_type),
            ('can_manage_permissions', 'Can manage user permissions', user_content_type),
            
            # Permissões de escritório/office
            ('can_manage_office_users', 'Can manage office users', user_content_type),
            ('can_view_office_reports', 'Can view office reports', user_content_type),
            ('can_manage_office_settings', 'Can manage office settings', profile_content_type),
            ('can_export_office_data', 'Can export office data', profile_content_type),
            
            # Permissões de usuário regular
            ('can_view_own_profile', 'Can view own profile', profile_content_type),
            ('can_edit_own_profile', 'Can edit own profile', profile_content_type),
            ('can_change_own_password', 'Can change own password', user_content_type),
        ]
        
        # Criar as permissões
        created_permissions = {}
        for codename, name, content_type in permissions_data:
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                content_type=content_type,
                defaults={'name': name}
            )
            created_permissions[codename] = permission
            if created:
                self.stdout.write(f'  Permissão criada: {codename}')
            else:
                self.stdout.write(f'  Permissão já existe: {codename}')
        
        # Definir os roles e suas permissões
        roles_config = {
            'system_admin': {
                'name': 'Administrador do Sistema',
                'permissions': [
                    # Permissões Django padrão
                    'add_user', 'change_user', 'delete_user', 'view_user',
                    'add_profile', 'change_profile', 'delete_profile', 'view_profile',
                    'add_group', 'change_group', 'delete_group', 'view_group',
                    'add_permission', 'change_permission', 'delete_permission', 'view_permission',
                    
                    # Permissões customizadas
                    'can_manage_system',
                    'can_view_all_users',
                    'can_delete_any_user',
                    'can_access_admin_panel',
                    'can_manage_permissions',
                    'can_manage_office_users',
                    'can_view_office_reports',
                    'can_manage_office_settings',
                    'can_export_office_data',
                    'can_view_own_profile',
                    'can_edit_own_profile',
                    'can_change_own_password',
                ]
            },
            'group_admin': {
                'name': 'Administrador de Grupo',
                'permissions': [
                    # Permissões para gerenciar grupo de clínicas
                    'add_user', 'change_user', 'view_user',
                    'add_profile', 'change_profile', 'view_profile',
                    'view_group', 'view_permission',
                    
                    # Permissões customizadas
                    'can_manage_office_users',
                    'can_view_office_reports',
                    'can_manage_office_settings',
                    'can_export_office_data',
                    'can_view_own_profile',
                    'can_edit_own_profile',
                    'can_change_own_password',
                ]
            },
            'office_admin': {
                'name': 'Administrador de Escritório',
                'permissions': [
                    # Permissões limitadas para usuários
                    'add_user', 'change_user', 'view_user',
                    'add_profile', 'change_profile', 'view_profile',
                    'view_group', 'view_permission',
                    
                    # Permissões customizadas
                    'can_manage_office_users',
                    'can_view_office_reports',
                    'can_manage_office_settings',
                    'can_export_office_data',
                    'can_view_own_profile',
                    'can_edit_own_profile',
                    'can_change_own_password',
                ]
            },
            'regular_user': {
                'name': 'Usuário Regular',
                'permissions': [
                    # Apenas permissões básicas
                    'view_profile',
                    
                    # Permissões customizadas
                    'can_view_own_profile',
                    'can_edit_own_profile',
                    'can_change_own_password',
                ]
            }
        }
        
        # Criar os roles
        for role_codename, config in roles_config.items():
            group, created = Group.objects.get_or_create(name=role_codename)
            
            if created:
                self.stdout.write(f'  Role criado: {role_codename}')
            else:
                self.stdout.write(f'  Role já existe: {role_codename}')
            
            # Limpar permissões existentes do role
            group.permissions.clear()
            
            # Adicionar permissões ao role
            for perm_codename in config['permissions']:
                try:
                    # Tentar buscar nas permissões customizadas primeiro
                    if perm_codename in created_permissions:
                        permission = created_permissions[perm_codename]
                    else:
                        # Buscar nas permissões padrão do Django
                        # Tentar diferentes content types comuns
                        permission = None
                        for ct in [user_content_type, profile_content_type]:
                            try:
                                permission = Permission.objects.get(
                                    codename=perm_codename,
                                    content_type=ct
                                )
                                break
                            except Permission.DoesNotExist:
                                continue
                        
                        # Se não encontrou nos content types específicos, buscar em geral
                        if not permission:
                            permission = Permission.objects.filter(
                                codename=perm_codename
                            ).first()
                        
                        if not permission:
                            raise Permission.DoesNotExist(f"Permissão {perm_codename} não encontrada")
                    
                    group.permissions.add(permission)
                    
                except Permission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'    Permissão não encontrada: {perm_codename}')
                    )
                    continue
            
            self.stdout.write(f'    Adicionadas {group.permissions.count()} permissões ao role {role_codename}')
        
        self.stdout.write(
            self.style.SUCCESS('Roles e permissões criados com sucesso!')
        )
        
        # Mostrar resumo
        self.stdout.write('\n=== RESUMO DOS ROLES ===')
        for group in Group.objects.filter(name__in=['system_admin', 'group_admin', 'office_admin', 'regular_user']):
            self.stdout.write(f'\n{group.name}:')
            for perm in group.permissions.all():
                self.stdout.write(f'  - {perm.codename}: {perm.name}')