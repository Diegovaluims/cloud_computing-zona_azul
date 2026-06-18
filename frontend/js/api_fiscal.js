/**
 * api_fiscal.js — Lógica para o Painel do Fiscal (MVP v2)
 */

const API_FISCAL = '/api/fiscal';
const API_AUTH = '/api/auth';

// --- Sessão ---
const idFiscal = localStorage.getItem('id_fiscal');
const nomeFiscal = localStorage.getItem('nome_fiscal');

if (!idFiscal) {
    window.location.href = 'index.html';
}

// Update UI
document.getElementById('nomeFiscalSidebar').textContent = `Fiscal: ${nomeFiscal}`;

document.getElementById('btnLogoutFiscal').addEventListener('click', async function () {
    try {
        await fetch(API_AUTH + '/fiscal/logout', { method: 'POST', credentials: 'include' });
    } catch(e) {}
    localStorage.removeItem('id_fiscal');
    localStorage.removeItem('nome_fiscal');
    window.location.href = 'index.html';
});

// --- Utilitários ---
function mostrarAlerta(elementoId, mensagem, tipo) {
    const el = document.getElementById(elementoId);
    el.innerHTML = mensagem;
    el.className = 'alert-glass mt-3 alert-' + tipo;
    setTimeout(function () {
        el.className = 'alert-glass mt-3 d-none';
    }, 4000);
}

// --- Consulta e Multas ---
document.getElementById('formFiscalizacao').addEventListener('submit', async function(e) {
    e.preventDefault();
    const placa = document.getElementById('inputPlacaFiscal').value.trim().toUpperCase();
    if (!placa) return;

    try {
        const resp = await fetch(`${API_FISCAL}/fiscalizacao/${placa}`, { credentials: 'include' });
        const data = await resp.json();

        const statusEl = document.getElementById('statusPlaca');
        const detalhesEl = document.getElementById('detalhesPlaca');
        const areaMulta = document.getElementById('areaMulta');
        const motivoOculto = document.getElementById('motivoMultaOculto');
        const alertMulta = document.getElementById('alertMulta');
        
        document.getElementById('resultadoConsulta').classList.remove('d-none');
        alertMulta.classList.add('d-none');
        areaMulta.classList.add('d-none');
        
        if (resp.ok) {
            statusEl.textContent = data.status;
            detalhesEl.textContent = data.detalhes;
            
            if (data.status === 'REGULAR') {
                statusEl.className = 'display-4 fw-bold text-success';
            } else {
                statusEl.className = 'display-4 fw-bold text-danger';
                areaMulta.classList.remove('d-none');
                motivoOculto.value = data.motivo_multa || 'OUTROS';
            }
        } else {
            statusEl.textContent = "Erro";
            statusEl.className = 'display-4 fw-bold text-warning';
            detalhesEl.textContent = data.detail || 'Não foi possível consultar a placa.';
        }

    } catch (err) {
        document.getElementById('resultadoConsulta').classList.remove('d-none');
        document.getElementById('statusPlaca').textContent = "Falha de Conexão";
        document.getElementById('detalhesPlaca').textContent = "Erro de rede ao conectar com a API do fiscal.";
    }
});

// Emitir Multa
document.getElementById('btnEmitirMulta').addEventListener('click', async function() {
    const placa = document.getElementById('inputPlacaFiscal').value.trim().toUpperCase();
    const motivo = document.getElementById('motivoMultaOculto').value;
    
    if(!confirm(`Confirma a emissão de multa (R$ 50,00) para o veículo ${placa}?`)) return;

    try {
        const resp = await fetch(API_FISCAL + '/multas', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ placa: placa, motivo: motivo, valor: 50.00 }),
            credentials: 'include'
        });

        if (resp.ok) {
            mostrarAlerta('alertMulta', 'Multa registrada com sucesso!', 'success');
            document.getElementById('areaMulta').classList.add('d-none');
        } else {
            const erro = await resp.json();
            mostrarAlerta('alertMulta', erro.detail || 'Erro ao registrar multa.', 'danger');
        }
    } catch (err) {
        mostrarAlerta('alertMulta', 'Erro de conexão.', 'danger');
    }
});
