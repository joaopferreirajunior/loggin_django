from django.db import models

# Modelo abstrato auditavel.
# Define campos criados, modificados e is_active.
# Usuários, devices e outros registros importantes devem ser deletados mudando is_active para false para manter seus registros.
# is_active não deve ser usado para outros fins (como e-mail não ativado, plano desativado, etc...).

class AuditModel(models.Model):
    created  = models.DateTimeField(auto_now_add=True)  # seta na criação
    modified = models.DateTimeField(auto_now=True)      # atualiza em cada save
    is_active = models.BooleanField(default=True)       # marca se o registro está ativo (desativar ao invés de deletar)

    class Meta:
        abstract = True