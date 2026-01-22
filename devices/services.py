import math
import boto3
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from devices.models import DeviceLocation
from typing import Tuple, Optional


class S3DeviceFileService:
    """
    Serviço para upload e gerenciamento de arquivos de dispositivos no AWS S3
    
    Segue a mesma estratégia do S3ImageService de users:
    - Usa IAM Roles da instância EC2 para autenticação
    - Gera URLs assinadas temporárias para acesso a arquivos privados
    - Gerencia upload e exclusão de arquivos (ícones, manuais, datasheets, etc)
    """
    
    def __init__(self):
        # Usa IAM Role da instância EC2 automaticamente
        self.s3_client = boto3.client(
            's3',
            region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1'),
            config=boto3.session.Config(signature_version='s3v4')
        )
        self.bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'loggin-media')
        self.presigned_url_expiration = getattr(settings, 'S3_PRESIGNED_URL_EXPIRATION', 3600)  # 1 hora
    
    def generate_presigned_url(self, s3_key: str, expiration: int = None) -> str:
        """
        Gera uma URL assinada temporária para acesso a um arquivo privado no S3
        
        Args:
            s3_key: Chave do objeto no S3
            expiration: Tempo de expiração em segundos (padrão: 1 hora)
            
        Returns:
            str: URL assinada temporária ou None se houver erro
        """
        try:
            if expiration is None:
                expiration = self.presigned_url_expiration
                
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return response
        except Exception as e:
            print(f"Erro ao gerar presigned URL para {s3_key}: {e}")
            return None
    
    def upload_file(self, file_obj, s3_key: str, content_type: str = None) -> Tuple[bool, str]:
        """
        Faz upload de um arquivo para o S3
        
        Args:
            file_obj: Objeto do arquivo (UploadedFile do Django)
            s3_key: Caminho/chave onde o arquivo será salvo no S3
            content_type: MIME type do arquivo (opcional)
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            return True, f"Arquivo enviado com sucesso: {s3_key}"
        except Exception as e:
            return False, f"Erro ao fazer upload: {str(e)}"
    
    def delete_file(self, s3_key: str) -> Tuple[bool, str]:
        """
        Remove um arquivo do S3
        
        Args:
            s3_key: Chave do objeto no S3
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True, f"Arquivo removido: {s3_key}"
        except Exception as e:
            return False, f"Erro ao deletar arquivo: {str(e)}"


def _haversine_meters(lat1, lon1, lat2, lon2):
    R = 6371000.0
    import math as m
    phi1 = m.radians(float(lat1)); phi2 = m.radians(float(lat2))
    dphi = m.radians(float(lat2) - float(lat1))
    dlmb = m.radians(float(lon2) - float(lon1))
    a = m.sin(dphi/2)**2 + m.cos(phi1)*m.cos(phi2)*m.sin(dlmb/2)**2
    return 2 * R * m.asin(m.sqrt(a))

@transaction.atomic
def save_location_if_moved(device, latitude, longitude, min_distance_m=100):
    """
    - Se deslocou > min_distance_m: cria um NOVO registro com read_at=now.
    - Caso contrário: ATUALIZA o read_at do último registro para now.
    Retorna (created: bool, obj: DeviceLocation).
    """
    now = timezone.now()

    last = (DeviceLocation.objects
            .select_for_update()
            .filter(device=device)
            .only("id", "latitude", "longitude", "read_at")
            .order_by("-read_at")
            .first())

    if last:
        dist = _haversine_meters(last.latitude, last.longitude, latitude, longitude)
        if dist <= min_distance_m:
            # Não cria novo; apenas “refresca” a última leitura
            last.read_at = now
            last.save(update_fields=["read_at"])
            return False, last

    # Não tinha último ponto OU deslocou mais que o limiar → cria novo
    obj = DeviceLocation.objects.create(
        device=device,
        latitude=latitude,
        longitude=longitude,
        read_at=now,
    )
    return True, obj