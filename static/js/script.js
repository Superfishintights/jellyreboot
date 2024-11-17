let isRestarting = false;
let credentials = null;

function getAuthHeader() {
    return 'Basic ' + btoa(credentials.username + ':' + credentials.password);
}

async function fetchWithAuth(url, options = {}) {
    if (!credentials) {
        throw new Error('Not authenticated');
    }
    
    const authOptions = {
        ...options,
        headers: {
            ...options.headers,
            'Authorization': getAuthHeader()
        }
    };
    
    const response = await fetch(url, authOptions);
    if (response.status === 401) {
        document.getElementById('content').classList.add('hidden');
        document.getElementById('loginForm').classList.remove('hidden');
        throw new Error('Authentication failed');
    }
    return response;
}

async function login(event) {
    event.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    credentials = { username, password };
    
    try {
        await fetchStatus();
        document.getElementById('loginForm').classList.add('hidden');
        document.getElementById('content').classList.remove('hidden');
    } catch (error) {
        alert('Login failed: ' + error.message);
        credentials = null;
    }
}

async function fetchStatus() {
    try {
        const response = await fetchWithAuth('/status');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        document.getElementById('status').innerText = data.status;
        document.getElementById('details').innerText = data.ps;
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('status').innerText = 'Error fetching status';
        throw error;
    }
}

async function restartContainer() {
    if (isRestarting) return;
    
    const button = document.getElementById('restartButton');
    button.disabled = true;
    isRestarting = true;

    try {
        const response = await fetchWithAuth('/restart', { 
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        alert(data.message);
    } catch (error) {
        console.error('Error:', error);
        alert('Error restarting container: ' + error.message);
    } finally {
        button.disabled = false;
        isRestarting = false;
        fetchStatus();
    }
}

// Initialize the page
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('content').classList.add('hidden');
    document.getElementById('loginForm').classList.remove('hidden');
});