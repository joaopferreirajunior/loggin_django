from django.db import models
from app.utils import AuditModel
from django.conf import settings

class Project(AuditModel):
    name = models.CharField(max_length=255)
    transfer_keys = models.JSONField(default=list, blank=True)
    features = models.JSONField(default=list, blank=True)
    clickhouse_id = models.UUIDField(unique=True, null=False, blank=False)
    metadata = models.TextField(default="", blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["name"]),
        ]
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    def __str__(self):
        return f"{self.name} ({self.clickhouse_id})"
    

class ProjectUser(AuditModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_users",
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="project_users",
    )

    class Meta:
        # Evita duplicidade (mesmo user no mesmo project mais de uma vez)
        constraints = [
            models.UniqueConstraint(fields=["user", "project"], name="uq_projectuser_user_project"),
        ]
        indexes = [
            models.Index(fields=["project", "user"]),
            models.Index(fields=["user", "project"]),
            models.Index(fields=["is_active"]),
        ]
        verbose_name = "Project user"
        verbose_name_plural = "Project users"

    def __str__(self):
        return f"{self.user_id} ↔ {self.project_id}"
    
