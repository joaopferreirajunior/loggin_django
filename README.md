# Medical San Loggin Django

Sistema backend loggin desenvolvido em Django.

## Início Rápido

### Ambiente Virtual
```bash
source loggin_venv/bin/activate
(Simula o ambiente da EC2 para testes locais)
```

### Configuração de Ambiente EC2

Configure as variáveis de ambiente no arquivo `.env`:

**Desenvolvimento (padrão):**
```bash
FRONTEND_URL=http://localhost:8000
```

**Produção:**
```bash
FRONTEND_URL=http://3.236.36.55:8000 
(Trocar IP para o domínio quando tiver um)
```

**Scripts de alternância de ambiente:**
```bash
# Desenvolvimento
./switch_env.sh dev

# Produção  
./switch_env.sh prod
```
Rodar na EC2 ou no ambiente local antes do build

## Docker

### Comandos Básicos

**Build inicial do container:**
```bash
docker compose up --build -d
```

**Restart simples (mudanças em views/templates):**
```bash
docker-compose restart django
```

**Rebuild com alterações:**
```bash
docker compose down && docker compose up --build -d
```

**Rebuild completo (alterações no requirements.txt):**
```bash
docker compose build --no-cache && docker compose up -d
```

### Gerenciamento de Containers

**Destruir containers manualmente:**
```bash
docker kill loggin_django
docker rm loggin_django

docker kill loggin_postgres
docker rm loggin_postgres
```

**Visualizar logs:**
```bash
# Logs do build
docker compose logs --tail=50

# Logs dos containers
docker logs loggin_django
docker logs loggin_postgres
```

## API Endpoints

### Autenticação

**Registro de usuário:**
```bash
# Desenvolvimento - Web
curl -X POST http://localhost:8000/api/web/v0/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "juanherrera", "email": "juan_herrera@tequila.com", "password": "@Senha123"}'

# Desenvolvimento - Mobile
curl -X POST http://localhost:8000/api/mobile/v0/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "juanherrera", "email": "juan_herrera@tequila.com", "password": "@Senha123"}'
```

**Login (JWT):**
```bash
# Desenvolvimento - Web
curl -X POST http://localhost:8000/api/web/v0/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "usuario", "password": "@Senha123"}'

# Desenvolvimento - Mobile  
curl -X POST http://localhost:8000/api/mobile/v0/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "usuario", "password": "@Senha123"}'

# Produção - Web
curl -X POST http://3.236.36.55:8000/api/web/v0/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "weber@blepol.com", "password": "medical25"}'
```

**Requisição autenticada:**
```bash
curl -X GET http://localhost:8000/api/web/v0/me/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI"
```

### Gerenciamento de Perfil

**Obter dados do usuário (com imagem):**
```bash
curl -X GET http://localhost:8000/users/api/v0/profile/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI"
```

**Upload de imagem de perfil:**
```bash
curl -X POST http://localhost:8000/users/api/v0/profile/image/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI" \
  -F "profile_image=@/caminho/para/imagem.jpg"
```

**Remover imagem de perfil:**
```bash
curl -X DELETE http://localhost:8000/users/api/v0/profile/image/ \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN_AQUI"
```

## Testando Interface Web com Upload de Imagem

### 1. Cadastrar e fazer login via interface web

1. Acesse: `http://localhost:8000/register/`
2. Cadastre um novo usuário
3. Faça login em: `http://localhost:8000/login/`

### 2. Visualizar dados na página inicial

1. Após o login, você será direcionado para: `http://localhost:8000/`
2. A página mostrará:
   - Foto de perfil (placeholder "Sem foto" se não houver imagem)
   - Dados básicos do usuário (nome, email, CPF, etc.)
   - Link para editar perfil

### 3. Fazer upload de imagem de perfil

1. Clique em "Editar Perfil" ou acesse: `http://localhost:8000/edit-profile/`
2. Na seção "Foto de Perfil":
   - Clique em "Escolher Foto"
   - Selecione uma imagem (JPEG, PNG, WebP até 5MB)
   - A imagem será automaticamente redimensionada e enviada para o S3
   - Você verá a confirmação de sucesso
3. Use o botão "Remover Foto" para deletar a imagem

### 4. Verificar se funcionou

1. Volte para a página inicial: `http://localhost:8000/`
2. A imagem de perfil deve aparecer no lugar do placeholder
3. A imagem está salva no S3 e a URL no banco de dados

## Upload de Imagem em Android (Flutter)

### Dependências necessárias

Adicione no `pubspec.yaml`:
```yaml
dependencies:
  http: ^1.1.0
  image_picker: ^1.0.4
  permission_handler: ^11.0.1
```

### Configuração de Permissões

**Android** (`android/app/src/main/AndroidManifest.xml`):
```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
```

**iOS** (`ios/Runner/Info.plist`):
```xml
<key>NSCameraUsageDescription</key>
<string>Este app precisa acessar a câmera para foto de perfil</string>
<key>NSPhotoLibraryUsageDescription</key>
<string>Este app precisa acessar a galeria para selecionar foto de perfil</string>
```

### Código Flutter Completo

```dart
import 'dart:io';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ProfileImageService {
  static const String baseUrl = 'http://3.236.36.55:8000'; // Produção
  // static const String baseUrl = 'http://localhost:8000'; // Desenvolvimento
  
  /// Seleciona imagem da galeria ou câmera
  static Future<File?> pickImage({bool fromCamera = false}) async {
    final picker = ImagePicker();
    final source = fromCamera ? ImageSource.camera : ImageSource.gallery;
    
    try {
      final pickedFile = await picker.pickImage(
        source: source,
        maxWidth: 1000,
        maxHeight: 1000,
        imageQuality: 80,
      );
      
      if (pickedFile != null) {
        return File(pickedFile.path);
      }
      return null;
    } catch (e) {
      print('Erro ao selecionar imagem: $e');
      return null;
    }
  }
  
  /// Faz upload da imagem de perfil
  static Future<Map<String, dynamic>> uploadProfileImage(File imageFile) async {
    try {
      // 1. Obter token JWT armazenado
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('access_token');
      
      if (token == null) {
        return {
          'success': false,
          'message': 'Token de autenticação não encontrado'
        };
      }
      
      // 2. Validar arquivo localmente
      final validation = await _validateImage(imageFile);
      if (!validation['valid']) {
        return {
          'success': false,
          'message': validation['message']
        };
      }
      
      // 3. Criar requisição multipart
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/users/api/v0/profile/image/')
      );
      
      // 4. Adicionar headers
      request.headers['Authorization'] = 'Bearer $token';
      
      // 5. Adicionar arquivo (nome do campo deve ser exatamente 'profile_image')
      request.files.add(
        await http.MultipartFile.fromPath(
          'profile_image',
          imageFile.path,
          filename: 'profile_${DateTime.now().millisecondsSinceEpoch}.jpg'
        )
      );
      
      // 6. Enviar requisição
      print('Enviando imagem para: $baseUrl/users/api/v0/profile/image/');
      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);
      
      print('Status Code: ${response.statusCode}');
      print('Response Body: ${response.body}');
      
      // 7. Processar resposta
      final responseData = json.decode(response.body);
      
      if (response.statusCode == 200) {
        return {
          'success': true,
          'message': responseData['detail'] ?? 'Imagem atualizada com sucesso',
          'image_url': responseData['image_url'],
          'user': responseData['user']
        };
      } else {
        return {
          'success': false,
          'message': responseData['detail'] ?? 'Erro desconhecido',
          'status_code': response.statusCode
        };
      }
      
    } catch (e) {
      print('Erro na requisição: $e');
      return {
        'success': false,
        'message': 'Erro de conexão: ${e.toString()}'
      };
    }
  }
  
  /// Remove a imagem de perfil
  static Future<Map<String, dynamic>> deleteProfileImage() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('access_token');
      
      if (token == null) {
        return {
          'success': false,
          'message': 'Token de autenticação não encontrado'
        };
      }
      
      final response = await http.delete(
        Uri.parse('$baseUrl/users/api/v0/profile/image/'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );
      
      final responseData = json.decode(response.body);
      
      if (response.statusCode == 200) {
        return {
          'success': true,
          'message': responseData['detail'] ?? 'Imagem removida com sucesso',
          'user': responseData['user']
        };
      } else {
        return {
          'success': false,
          'message': responseData['detail'] ?? 'Erro ao remover imagem'
        };
      }
      
    } catch (e) {
      return {
        'success': false,
        'message': 'Erro de conexão: ${e.toString()}'
      };
    }
  }
  
  /// Validação local da imagem
  static Future<Map<String, dynamic>> _validateImage(File imageFile) async {
    // Verificar se arquivo existe
    if (!await imageFile.exists()) {
      return {'valid': false, 'message': 'Arquivo de imagem não encontrado'};
    }
    
    // Verificar tamanho (máx 5MB)
    final fileSize = await imageFile.length();
    if (fileSize > 5 * 1024 * 1024) {
      return {
        'valid': false, 
        'message': 'Arquivo muito grande. Máximo permitido: 5MB'
      };
    }
    
    // Verificar extensão
    final extension = imageFile.path.split('.').last.toLowerCase();
    final allowedExtensions = ['jpg', 'jpeg', 'png', 'webp'];
    if (!allowedExtensions.contains(extension)) {
      return {
        'valid': false,
        'message': 'Formato não permitido. Use: JPG, PNG ou WebP'
      };
    }
    
    return {'valid': true, 'message': 'Arquivo válido'};
  }
}

/// Widget de exemplo para usar o serviço
class ProfileImageWidget extends StatefulWidget {
  @override
  _ProfileImageWidgetState createState() => _ProfileImageWidgetState();
}

class _ProfileImageWidgetState extends State<ProfileImageWidget> {
  String? _currentImageUrl;
  bool _isUploading = false;
  
  /// Mostra dialog para escolher fonte da imagem
  Future<void> _showImageSourceDialog() async {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text('Selecionar Imagem'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ListTile(
                leading: Icon(Icons.photo_library),
                title: Text('Galeria'),
                onTap: () {
                  Navigator.pop(context);
                  _handleImageUpload(fromCamera: false);
                },
              ),
              ListTile(
                leading: Icon(Icons.camera_alt),
                title: Text('Câmera'),
                onTap: () {
                  Navigator.pop(context);
                  _handleImageUpload(fromCamera: true);
                },
              ),
            ],
          ),
        );
      },
    );
  }
  
  /// Gerencia o processo de upload
  Future<void> _handleImageUpload({bool fromCamera = false}) async {
    setState(() {
      _isUploading = true;
    });
    
    try {
      // 1. Selecionar imagem
      final imageFile = await ProfileImageService.pickImage(
        fromCamera: fromCamera
      );
      
      if (imageFile == null) {
        _showSnackBar('Nenhuma imagem selecionada', isError: true);
        return;
      }
      
      // 2. Fazer upload
      final result = await ProfileImageService.uploadProfileImage(imageFile);
      
      // 3. Mostrar resultado
      if (result['success']) {
        setState(() {
          _currentImageUrl = result['image_url'];
        });
        _showSnackBar(result['message']);
      } else {
        _showSnackBar(result['message'], isError: true);
      }
      
    } catch (e) {
      _showSnackBar('Erro inesperado: $e', isError: true);
    } finally {
      setState(() {
        _isUploading = false;
      });
    }
  }
  
  /// Remove a imagem atual
  Future<void> _handleImageDelete() async {
    final result = await ProfileImageService.deleteProfileImage();
    
    if (result['success']) {
      setState(() {
        _currentImageUrl = null;
      });
      _showSnackBar(result['message']);
    } else {
      _showSnackBar(result['message'], isError: true);
    }
  }
  
  /// Mostra mensagem para o usuário
  void _showSnackBar(String message, {bool isError = false}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: isError ? Colors.red : Colors.green,
        duration: Duration(seconds: 3),
      ),
    );
  }
  
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Preview da imagem
        Container(
          width: 120,
          height: 120,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(color: Colors.grey[300]!, width: 2),
          ),
          child: ClipOval(
            child: _currentImageUrl != null
                ? Image.network(
                    _currentImageUrl!,
                    fit: BoxFit.cover,
                    loadingBuilder: (context, child, loadingProgress) {
                      if (loadingProgress == null) return child;
                      return Center(
                        child: CircularProgressIndicator(
                          value: loadingProgress.expectedTotalBytes != null
                              ? loadingProgress.cumulativeBytesLoaded /
                                  loadingProgress.expectedTotalBytes!
                              : null,
                        ),
                      );
                    },
                    errorBuilder: (context, error, stackTrace) {
                      return Icon(Icons.person, size: 60, color: Colors.grey);
                    },
                  )
                : Icon(Icons.person, size: 60, color: Colors.grey),
          ),
        ),
        
        SizedBox(height: 16),
        
        // Botões de ação
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            ElevatedButton.icon(
              onPressed: _isUploading ? null : _showImageSourceDialog,
              icon: _isUploading 
                  ? SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : Icon(Icons.upload),
              label: Text(_isUploading ? 'Enviando...' : 'Alterar'),
            ),
            
            SizedBox(width: 12),
            
            if (_currentImageUrl != null)
              ElevatedButton.icon(
                onPressed: _isUploading ? null : _handleImageDelete,
                icon: Icon(Icons.delete),
                label: Text('Remover'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red[400],
                ),
              ),
          ],
        ),
      ],
    );
  }
}
```

### Exemplo de Uso

```dart
class ProfileScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Perfil')),
      body: Center(
        child: ProfileImageWidget(),
      ),
    );
  }
}
```

### Tratamento de Erros Comuns

```dart
// Verificar conectividade antes do upload
import 'package:connectivity_plus/connectivity_plus.dart';

Future<bool> _checkConnectivity() async {
  var connectivityResult = await Connectivity().checkConnectivity();
  return connectivityResult != ConnectivityResult.none;
}

// Usar antes do upload
if (!await _checkConnectivity()) {
  _showSnackBar('Sem conexão com a internet', isError: true);
  return;
}
```

### Dicas Importantes

1. **Token JWT**: Certifique-se de que o token está válido e não expirou
2. **Tamanho**: Backend aceita máximo 5MB, valide localmente primeiro
3. **Formatos**: JPG, PNG, WebP são suportados
4. **Redimensionamento**: Backend redimensiona automaticamente para 800x800px
5. **Cache**: Use `cached_network_image` para melhor performance:

```yaml
dependencies:
  cached_network_image: ^3.3.0
```

```dart
import 'package:cached_network_image/cached_network_image.dart';

CachedNetworkImage(
  imageUrl: _currentImageUrl!,
  placeholder: (context, url) => CircularProgressIndicator(),
  errorWidget: (context, url, error) => Icon(Icons.person),
  fit: BoxFit.cover,
)
```

### Recuperação de Senha

**Solicitar recuperação:**
```bash
# Web
curl -X POST http://localhost:8000/api/web/v0/recoverypassword/ \
  -H "Content-Type: application/json" \
  -d '{"email": "usuario@email.com"}'

# Mobile
curl -X POST http://localhost:8000/api/mobile/v0/recoverypassword/ \
  -H "Content-Type: application/json" \
  -d '{"email": "usuario@email.com"}'
```

**Resposta (desenvolvimento com tokens de teste):**
```json
{
  "detail": "Se o email usuario@email.com estiver registrado, você receberá instruções para recuperação de senha.",
  "test_link": "http://localhost:8000/api/web/v0/validatetoken/?token=abc123token",
  "test_token": "abc123token"
}
```

**Validar token:**
```bash
curl -X GET "http://localhost:8000/api/web/v0/validatetoken/?token=abc123token"
```

**Reset de senha:**
```bash
curl -X POST http://localhost:8000/api/web/v0/resetpassword/ \
  -H "Content-Type: application/json" \
  -d '{"token": "abc123token", "password": "novaSenha123"}'
```

### Fluxo de Recuperação de Senha

1. **Solicitação**: Usuário acessa `/recovery-password/` e informa email
2. **Email**: Sistema envia link: `/api/web/v0/validatetoken/?token=abc123`
3. **Validação**: Usuário clica no link do email
4. **Redirecionamento automático**:
   - Token válido → `/reset-password/?token=abc123`
   - Token inválido → `/recovery-password/?error=token_invalid`
5. **Nova senha**: Usuário define nova senha na página de reset
6. **Finalização**: Token é invalidado após uso bem-sucedido

## Documentação da API

**Gerar schema OpenAPI:**
```bash
python manage.py spectacular --format openapi --file openapi-schema.yaml
```

**Visualizar documentação:**
- Clique com botão direito em `openapi-schema.yaml`
- Selecione "Preview Swagger"

**URLs da documentação (após configuração):**
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`  
- Schema JSON: `http://localhost:8000/api/schema/`

### Organização da Documentação

A API está organizada em seções distintas:

**Web APIs** (`/api/web/v0/`):
- **Web - Auth**: Login, registro, recuperação de senha para aplicação web
- **Web - User**: Gerenciamento de usuários e perfis para aplicação web

**Mobile APIs** (`/api/mobile/v0/`):
- **Mobile - Auth**: Login, registro, recuperação de senha para aplicação mobile  
- **Mobile - User**: Gerenciamento de usuários e perfis para aplicação mobile

**User Management** (`/users/api/v0/`):
- Upload e gerenciamento de imagens de perfil
- Funcionalidades gerais de usuários (comum a web e mobile)

## Deploy AWS EC2

### Pré-requisitos

1. **Código no GitHub**: Sempre faça push das alterações antes do deploy
2. **Branch**: Verifique o branch configurado em `update.sh` (ex: `BRANCH="dev"`)

### Preparação local antes do deploy

**1. Ativar ambiente virtual (WSL):**
```bash
source loggin_venv/bin/activate
```

**2. Atualizar dependências:**
```bash
pip install -r requirements.txt
```

**3. Fazer migrações:**
```bash
python manage.py makemigrations
```

### Execução do Deploy

**Opção 1: Deploy a partir da máquina local (recomendado):**
```bash
./deploy_aws.sh
```

**Opção 2: Puxar deploy direto na AWS:**
```bash
# Conectar via SSH
ssh -i ~/.ssh/loggin-key.pem ubuntu@ec2-3-236-36-55.compute-1.amazonaws.com

# Executar update
./update.sh
```

> **Nota**: Para WSL, copie a chave SSH para dentro da máquina virtual, pois os caminhos Windows não são compatíveis.

## Estrutura do Projeto

```
loggin_django/
├── app/                 # Configurações principais  
├── loggin/              # App principal consolidado
│   ├── api/             # APIs organizadas por cliente
│   │   ├── web/v0/      # Endpoints para aplicação web
│   │   └── mobile/v0/   # Endpoints para aplicação mobile
│   └── templates/       # Templates HTML
├── users/               # Gerenciamento de usuários e perfis
│   ├── services.py      # Serviço S3 para upload de imagens
│   └── api/v0/          # APIs de usuários (upload de imagem)
├── devices/             # APIs para dados de equipamentos
├── projects/            # APIs para projetos
├── docker-compose.yml   # Configuração Docker
├── requirements.txt     # Dependências Python
└── update.sh           # Script de deploy automático
```

## Configuração AWS S3

### Pré-requisitos

1. **Bucket S3**: Crie um bucket no AWS S3 para armazenar imagens
2. **IAM Role**: Configure uma IAM Role para a instância EC2 com permissões S3
3. **Variáveis de ambiente**: Configure no arquivo `.env`

### IAM Role para EC2

Crie uma IAM Role com as seguintes permissões e anexe à instância EC2:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl",
                "s3:GetObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::loggin-media/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::loggin-media"
        }
    ]
}
```

### Configuração do Bucket

- **Nome**: `loggin-media` (ou conforme configurado no .env)
- **Região**: `us-east-1` (ou conforme configurado no .env)
- **Acesso público**: Configure para permitir leitura pública das imagens
- **CORS**: Configure para permitir uploads do frontend
- **Lifecycle**: Configure rules para limpeza automática (opcional)

### Variáveis de Ambiente

Adicione ao arquivo `.env`:
```bash
# Configurações do S3 Bucket
# AWS_ACCESS_KEY_ID e AWS_SECRET_ACCESS_KEY foram removidos
# O sistema agora usa IAM Role da instância EC2 automaticamente
AWS_STORAGE_BUCKET_NAME=loggin-media
AWS_S3_REGION_NAME=us-east-1
```

### Testando a Configuração

Para verificar se a IAM Role e S3 estão configurados corretamente:

```bash
# Execute o comando de teste
python manage.py test_s3

# Output esperado em caso de sucesso:
# Testando configuração AWS S3...
# Conexão S3 OK - IAM Role configurada corretamente
# Bucket: loggin-media
# Região: us-east-1
```

### Troubleshooting

**Erro: "IAM Role não encontrada"**
- Verifique se a instância EC2 tem uma IAM Role anexada
- Vá no console AWS → EC2 → Instances → Actions → Security → Modify IAM role

**Erro: "IAM Role não tem permissões suficientes"**
- Verifique se a IAM Role tem as permissões S3 listadas acima
- Teste com uma policy mais ampla temporariamente: `AmazonS3FullAccess`

**Erro: "Bucket não existe"**
- Verifique se o nome do bucket no `.env` está correto
- Verifique se o bucket existe na região configurada
```
