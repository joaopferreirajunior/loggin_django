import boto3
import uuid
import os
from PIL import Image, ImageOps
from io import BytesIO
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from typing import Tuple, Optional

class S3ImageService:
    """
    Serviço para upload, redimensionamento e gerenciamento de imagens no AWS S3
    
    SEGURANÇA: Este serviço usa IAM Roles da instância EC2 para autenticação,
    eliminando a necessidade de armazenar chaves de acesso no código ou arquivos.
    
    Para funcionar corretamente:
    1. A instância EC2 deve ter uma IAM Role anexada
    2. A IAM Role deve ter permissões para S3 (s3:PutObject, s3:GetObject, s3:DeleteObject)
    3. O bucket S3 deve existir e ter as configurações adequadas
    """
    
    def __init__(self):
        # Usa IAM Role da instância EC2 automaticamente
        # O boto3 detecta automaticamente as credenciais da IAM Role quando roda na EC2
        self.s3_client = boto3.client(
            's3',
            region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1'),
            config=boto3.session.Config(signature_version='s3v4')
        )
        self.bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'loggin-media')
        self.max_size = getattr(settings, 'PROFILE_IMAGE_MAX_SIZE', (800, 800))  # pixels
        self.quality = getattr(settings, 'PROFILE_IMAGE_QUALITY', 85)  # qualidade JPEG
        self.max_file_size = getattr(settings, 'PROFILE_IMAGE_MAX_FILE_SIZE', 5 * 1024 * 1024)  # 5MB
        self.presigned_url_expiration = getattr(settings, 'S3_PRESIGNED_URL_EXPIRATION', 3600)  # 1 hora
    
    def generate_presigned_url(self, s3_key: str, expiration: int = None) -> str:
        """
        Gera uma URL assinada temporária para acesso a um objeto privado no S3
        
        Args:
            s3_key: Chave do objeto no S3
            expiration: Tempo de expiração em segundos (padrão: configurado em settings)
            
        Returns:
            str: URL assinada temporária
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
    
    def test_s3_connection(self) -> Tuple[bool, str]:
        """
        Testa se a conexão com S3 está funcionando e se a IAM Role tem as permissões adequadas
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Tenta listar objetos do bucket para verificar permissões
            self.s3_client.list_objects_v2(Bucket=self.bucket_name, MaxKeys=1)
            return True, "Conexão S3 OK - IAM Role configurada corretamente"
        except Exception as e:
            error_msg = str(e)
            if "NoCredentialsError" in error_msg:
                return False, "IAM Role não encontrada ou não anexada à instância EC2"
            elif "AccessDenied" in error_msg:
                return False, "IAM Role não tem permissões suficientes para S3"
            elif "NoSuchBucket" in error_msg:
                return False, f"Bucket '{self.bucket_name}' não existe ou não é acessível"
            else:
                return False, f"Erro de conexão S3: {error_msg}"
    
    def validate_image(self, image_file) -> Tuple[bool, str]:
        """
        Valida se o arquivo é uma imagem válida
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        # Verifica tamanho do arquivo
        if image_file.size > self.max_file_size:
            return False, f"Arquivo muito grande. Máximo: {self.max_file_size / (1024*1024):.1f}MB"
        
        # Verifica tipo de arquivo
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        if image_file.content_type not in allowed_types:
            return False, f"Tipo de arquivo não permitido. Permitidos: {', '.join(allowed_types)}"
        
        # Verifica se é realmente uma imagem válida
        try:
            image = Image.open(image_file)
            image.verify()  # Verifica se não está corrompida
            return True, "OK"
        except Exception as e:
            return False, f"Arquivo de imagem inválido: {str(e)}"
    
    def resize_image(self, image_file) -> BytesIO:
        """
        Redimensiona a imagem mantendo proporção, corrige orientação EXIF e otimiza para web
        
        Args:
            image_file: Arquivo de imagem uploadado
            
        Returns:
            BytesIO: Imagem processada em buffer
        """
        # Abre a imagem
        image = Image.open(image_file)
        
        # CORREÇÃO EXIF: Aplica rotação baseada nos metadados EXIF
        # Isso resolve o problema de imagens que rotacionam automaticamente
        image = ImageOps.exif_transpose(image)
        
        # Converte para RGB se necessário (remove canal alpha)
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if len(image.split()) > 3 else None)
            image = background
        
        # Redimensiona mantendo proporção
        image.thumbnail(self.max_size, Image.Resampling.LANCZOS)
        
        # Salva em buffer com otimização, preservando metadados EXIF
        buffer = BytesIO()
        
        # Tenta preservar EXIF se disponível
        exif_data = None
        try:
            if hasattr(image, '_getexif') and image._getexif() is not None:
                exif_data = image.info.get('exif')
        except:
            pass  # Se houver erro ao ler EXIF, continua sem ele
        
        # Salva com ou sem EXIF
        save_kwargs = {
            'format': 'JPEG', 
            'quality': self.quality,
            'optimize': True,
            'progressive': True
        }
        
        if exif_data:
            save_kwargs['exif'] = exif_data
            
        image.save(buffer, **save_kwargs)
        buffer.seek(0)
        
        return buffer
    
    def generate_s3_key(self, user_id: int, original_filename: str) -> str:
        """
        Gera uma chave única para o arquivo no S3
        
        Args:
            user_id: ID do usuário
            original_filename: Nome original do arquivo
            
        Returns:
            str: Chave S3 (path) para o arquivo
        """
        # Extrai extensão original ou usa .jpg como padrão
        file_ext = os.path.splitext(original_filename)[1].lower()
        if not file_ext or file_ext not in ['.jpg', '.jpeg', '.png', '.webp']:
            file_ext = '.jpg'
        
        # Gera nome único
        unique_id = str(uuid.uuid4())
        filename = f"avatar_{unique_id}{file_ext}"
        
        # Organiza por pastas: profiles/user_{id}/filename
        return f"profiles/user_{user_id}/{filename}"
    
    def upload_to_s3(self, image_buffer: BytesIO, s3_key: str) -> bool:
        """
        Faz upload da imagem para o S3
        
        Args:
            image_buffer: Buffer da imagem processada
            s3_key: Chave/path no S3
            
        Returns:
            bool: Sucesso do upload
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=image_buffer,
                ContentType='image/jpeg',
                CacheControl='max-age=31536000',  # Cache por 1 ano
                Metadata={
                    'uploaded_by': 'medical_san_app',
                    'content_type': 'profile_image'
                }
            )
            return True
        except Exception as e:
            print(f"Erro ao fazer upload para S3: {e}")
            return False
    
    def delete_from_s3(self, s3_key: str) -> bool:
        """
        Remove arquivo do S3
        
        Args:
            s3_key: Chave/path do arquivo no S3
            
        Returns:
            bool: Sucesso da remoção
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except Exception as e:
            print(f"Erro ao deletar arquivo do S3: {e}")
            return False
    
    def process_and_upload_profile_image(self, user_id: int, image_file) -> Tuple[bool, str, Optional[str]]:
        """
        Pipeline completo: validação, processamento e upload
        
        Args:
            user_id: ID do usuário
            image_file: Arquivo de imagem uploadado
            
        Returns:
            Tuple[bool, str, Optional[str]]: (success, message, s3_key_or_none)
        """
        # 1. Validação
        is_valid, error_message = self.validate_image(image_file)
        if not is_valid:
            return False, error_message, None
        
        # 2. Processamento
        try:
            image_buffer = self.resize_image(image_file)
        except Exception as e:
            return False, f"Erro ao processar imagem: {str(e)}", None
        
        # 3. Gerar chave S3
        s3_key = self.generate_s3_key(user_id, image_file.name)
        
        # 4. Upload
        upload_success = self.upload_to_s3(image_buffer, s3_key)
        if not upload_success:
            return False, "Erro ao fazer upload da imagem", None
        
        return True, "Imagem uploaded com sucesso", s3_key


def get_profile_image_url(s3_key: str) -> str:
    """
    Utility function para gerar URL completa da imagem
    
    Args:
        s3_key: Chave do arquivo no S3
        
    Returns:
        str: URL completa da imagem
    """
    bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'loggin-media')
    region = getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
    return f"https://{bucket_name}.s3.{region}.amazonaws.com/{s3_key}"