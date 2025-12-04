# loggin/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
import requests


#Views de páginas HTML

@login_required(login_url='login_page')
def home(request):
    return render(request, "home.html", {"mensagem": "Página inicial (testando API)"})

def login_page(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # URL ABSOLUTA para a API WEB de login
        try:
            api_url = request.build_absolute_uri(reverse("api_web_login"))
        except:
            # fallback para URL hardcoded se reverse falhar
            api_url = request.build_absolute_uri("/api/web/v0/login/")

        try:
            resp = requests.post(
                api_url,
                json={"username": username, "password": password},
                timeout=8,
            )
            # tenta parsear JSON sem quebrar
            data = {}
            if resp.headers.get("content-type", "").startswith("application/json"):
                try:
                    data = resp.json()
                except ValueError:
                    data = {}

            if resp.status_code == 200:
                # cria sessão no Django para o navegador
                user = authenticate(request, username=username, password=password)
                if user:
                    login(request, user)
                    return redirect("home")
                return render(request, "login.html", {"error": "Falha ao criar sessão local."})
            else:
                msg = data.get("detail") or "Usuário ou senha incorretos."
                return render(request, "login.html", {"error": msg})

        except requests.RequestException as e:
            return render(request, "login.html", {"error": f"Erro de conexão com a API: {e}"})

    return render(request, "login.html")

def register_page(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        cpf = request.POST.get("cpf")
        birth = request.POST.get("birth")
        phone = request.POST.get("phone")

        # URL ABSOLUTA para a API WEB de cadastro
        try:
            api_url = request.build_absolute_uri(reverse("api_web_register"))
        except:
            # fallback para URL hardcoded se reverse falhar
            api_url = request.build_absolute_uri("/api/web/v0/register/")

        try:
            payload = {"username": username, "email": email, "password": password}
            # adiciona campos opcionais se presentes
            if cpf:
                payload["cpf"] = cpf
            if birth:
                payload["birth"] = birth
            if phone:
                payload["phone"] = phone

            print(f"DEBUG: Enviando payload para registro: {payload}")
            print(f"DEBUG: URL da API: {api_url}")

            resp = requests.post(
                api_url,
                json=payload,
                timeout=8,
            )
            
            print(f"DEBUG: Status da resposta: {resp.status_code}")
            print(f"DEBUG: Headers da resposta: {resp.headers}")
            print(f"DEBUG: Conteúdo da resposta: {resp.text}")
            # parse seguro do JSON
            data = {}
            if resp.headers.get("content-type", "").startswith("application/json"):
                try:
                    data = resp.json()
                except ValueError:
                    data = {}

            if resp.status_code == 201:
                # login automático após cadastro
                user = authenticate(request, username=username, password=password)
                if user:
                    login(request, user)
                return redirect("home")

            # montar mensagem de erro vinda da API
            error_msg = (
                (isinstance(data.get("username"), list) and data["username"][0]) or data.get("username") or
                (isinstance(data.get("email"), list) and data["email"][0]) or data.get("email") or
                (isinstance(data.get("password"), list) and data["password"][0]) or data.get("password") or
                data.get("detail") or
                f"Erro HTTP {resp.status_code}"
            )
            return render(request, "register.html", {"error": str(error_msg)})

        except requests.RequestException as e:
            return render(request, "register.html", {"error": f"Erro de conexão com a API: {e}"})

    return render(request, "register.html")

def logout_view(request):
    logout(request)
    return redirect('login_page')

@login_required(login_url='login_page')
def edit_profile_page(request):
    return render(request, "edit_profile.html")

def recovery_password_page(request):
    """Página para solicitar recuperação de senha"""
    return render(request, "recovery_password.html")

def reset_password_page(request):
    """Página para redefinir senha com token"""
    return render(request, "reset_password.html")
