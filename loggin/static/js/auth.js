/**
 * Funções de autenticação e gerenciamento de tokens JWT
 */

// Armazena tokens após login/registro
function storeAuthTokens(accessToken, refreshToken, userData) {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    localStorage.setItem('user', JSON.stringify(userData));
    
    // Também no sessionStorage para compatibilidade
    sessionStorage.setItem('user', JSON.stringify(userData));
}

// Recupera token de acesso
function getAccessToken() {
    return localStorage.getItem('access_token');
}

// Recupera token de refresh
function getRefreshToken() {
    return localStorage.getItem('refresh_token');
}

// Recupera dados do usuário
function getUserData() {
    const userData = localStorage.getItem('user');
    return userData ? JSON.parse(userData) : null;
}

// Limpa dados de autenticação
function clearAuthData() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    sessionStorage.removeItem('user');
}

// Verifica se o usuário está logado
function isAuthenticated() {
    return !!(getAccessToken() && getRefreshToken());
}

// Faz requisições autenticadas com token JWT
async function makeAuthenticatedRequest(url, options = {}) {
    const token = getAccessToken();
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : '',
            ...options.headers
        }
    };
    
    return fetch(url, { ...defaultOptions, ...options });
}

// Renova o token de acesso usando o refresh token
async function refreshAccessToken() {
    const refreshToken = getRefreshToken();
    if (!refreshToken) {
        clearAuthData();
        return null;
    }
    
    try {
        const response = await fetch('/api/web/v0/token/refresh/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh: refreshToken })
        });
        
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access);
            return data.access;
        } else {
            clearAuthData();
            return null;
        }
    } catch (error) {
        console.error('Erro ao renovar token:', error);
        clearAuthData();
        return null;
    }
}

// Logout
async function logout() {
    try {
        // Tenta fazer logout no servidor
        await fetch('/api/web/v0/logout/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getAccessToken()}`
            }
        });
    } catch (error) {
        console.error('Erro no logout:', error);
    } finally {
        clearAuthData();
        window.location.href = '/login/';
    }
}