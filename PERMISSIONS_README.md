# Sistema de Permissões de Usuários

Este documento descreve como funciona o sistema de permissões implementado, compatível com `user.has_perm()` e `user.get_all_permissions()` do Django.

## Grupos de Usuários

### 1. **system_admin** (Administrador do Sistema)
- **Descrição**: Acesso total ao sistema
- **Permissões**:
  - Gerenciar todos os usuários (criar, editar, deletar)
  - Gerenciar grupos e permissões
  - Acessar painel administrativo
  - Todas as permissões de office_admin e regular_user

### 2. **office_admin** (Administrador de Escritório) 
- **Descrição**: Gerencia usuários e configurações do escritório
- **Permissões**:
  - Gerenciar usuários do escritório
  - Ver relatórios do escritório
  - Gerenciar configurações do escritório
  - Exportar dados do escritório
  - Todas as permissões de regular_user

### 3. **regular_user** (Usuário Regular)
- **Descrição**: Usuário padrão com acesso básico
- **Permissões**:
  - Ver próprio perfil
  - Editar próprio perfil
  - Alterar própria senha

## Como Usar

### 1. Configurar o Sistema (Uma vez)
```bash
cd "c:\Medical San\loggin_django"
python manage.py setup_user_groups
```

### 2. Verificar Permissões no Código

```python
# Verificar se usuário tem permissão específica
if request.user.has_perm('auth.can_manage_system'):
    # Usuário é system_admin
    pass

# Verificar papel do usuário
user_profile = request.user.profile
role = user_profile.get_user_role()  # 'system_admin', 'office_admin', 'regular_user'

# Verificações rápidas
if user_profile.is_system_admin():
    # Lógica para system_admin
    pass
elif user_profile.is_office_admin():
    # Lógica para office_admin
    pass
elif user_profile.is_regular_user():
    # Lógica para regular_user
    pass

# Verificar capacidades específicas
if user_profile.can_manage_users():
    # Pode gerenciar usuários (system_admin ou office_admin)
    pass
```

### 3. Atribuir Papéis via API

```javascript
// Atribuir papel via API (apenas system_admin)
fetch('/api/v0/assign-role/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
    },
    body: JSON.stringify({
        user_id: 123,
        role: 'office_admin'  // 'system_admin', 'office_admin', 'regular_user'
    })
});
```

### 4. Verificar Permissões via API

```javascript
// Buscar permissões do usuário atual
fetch('/api/v0/me/permissions/')
.then(response => response.json())
.then(data => {
    console.log('Papel:', data.user_role);
    console.log('É admin?', data.is_system_admin);
    console.log('Permissões:', data.permissions);
});
```

## Decorators para Views

```python
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin

# Para function-based views
@permission_required('auth.can_manage_system')
def admin_only_view(request):
    pass

@permission_required('auth.can_manage_office_users')
def office_admin_view(request):
    pass

# Para class-based views
class AdminOnlyView(PermissionRequiredMixin, View):
    permission_required = 'auth.can_manage_system'
```

## Templates

```html
{% if user.has_perm:'auth.can_manage_system' %}
    <a href="/admin/">Painel Admin</a>
{% endif %}

{% if user.profile.is_office_admin %}
    <a href="/office/">Gerenciar Escritório</a>
{% endif %}
```

## Permissões Disponíveis

### System Admin
- `auth.can_manage_system`
- `auth.can_view_all_users`
- `auth.can_delete_any_user`
- `auth.can_access_admin_panel`
- `auth.can_manage_permissions`
- (+ todas as permissões abaixo)

### Office Admin  
- `auth.can_manage_office_users`
- `auth.can_view_office_reports`
- `users.can_manage_office_settings`
- `users.can_export_office_data`
- (+ todas as permissões abaixo)

### Regular User
- `users.can_view_own_profile`
- `users.can_edit_own_profile`
- `auth.can_change_own_password`

## Atribuir Papel Programaticamente

```python
from users.models import UserProfile

# Atribuir papel a um usuário
user = User.objects.get(username='joao')
UserProfile.assign_role(user, 'office_admin')

# Verificar papel
profile = user.profile
print(profile.get_user_role())  # 'office_admin'
```

## APIs Disponíveis

- `GET /api/v0/me/permissions/` - Retorna permissões do usuário atual
- `POST /api/v0/assign-role/` - Atribui papel a um usuário (requer permissão)

## Troubleshooting

1. **Erro "Permission not found"**: Execute `python manage.py setup_user_groups`
2. **Usuário sem papel**: Atribua papel usando `UserProfile.assign_role()`
3. **Permissões não funcionam**: Verifique se o usuário está no grupo correto