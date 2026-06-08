/**
 * api_fiscal.js — Integração do Painel do Fiscal com a API (porta 8001)
 *
 * Função: Consulta de placa para verificar situação (REGULAR/IRREGULAR).
 * Segurança: usa textContent e createElement para inserção no DOM (sem innerHTML).
 */

var API_FISCAL = 'http://54.20.72.204:8001';

// --- Utilitários ---
function mostrarAlertaFiscal(mensagem, tipo) {
    var el = document.getElementById('alertFiscal');
    el.textContent = mensagem;
    el.className = 'alert alert-' + tipo + ' mt-3';
    setTimeout(function () {
        el.className = 'alert d-none mt-3';
    }, 3000);
}

// --- Fiscalização ---
document.getElementById('formFiscalizar').addEventListener('submit', async function (e) {
    e.preventDefault();

    var placa = document.getElementById('inputPlacaFiscal').value.trim().toUpperCase();

    if (!placa) {
        mostrarAlertaFiscal('Digite uma placa válida.', 'warning');
        return;
    }

    try {
        var resp = await fetch(API_FISCAL + '/fiscalizacao/' + encodeURIComponent(placa));

        if (!resp.ok) {
            mostrarAlertaFiscal('Erro ao consultar a placa.', 'danger');
            return;
        }

        var dados = await resp.json();
        var container = document.getElementById('resultadoFiscalizacao');
        var card = document.getElementById('cardResultado');
        var statusTexto = document.getElementById('statusTexto');
        var detalhesTexto = document.getElementById('detalhesTexto');
        var placaConsultada = document.getElementById('placaConsultada');

        container.classList.remove('d-none');

        if (dados.status === 'REGULAR') {
            card.className = 'card border-success';
            statusTexto.textContent = '✅ REGULAR';
            statusTexto.className = 'mb-2 text-success';
        } else {
            card.className = 'card border-danger';
            statusTexto.textContent = '❌ IRREGULAR';
            statusTexto.className = 'mb-2 text-danger';
        }

        detalhesTexto.textContent = dados.detalhes;
        placaConsultada.textContent = 'Placa consultada: ' + placa;

        // Adiciona ao histórico
        adicionarHistorico(placa, dados.status);

    } catch (err) {
        mostrarAlertaFiscal('Erro de conexão com a API. Ela está rodando?', 'danger');
    }
});

// --- Histórico (local, em memória) ---
function adicionarHistorico(placa, status) {
    var tbody = document.getElementById('tabelaHistorico');
    var semHistorico = document.getElementById('semHistorico');

    semHistorico.classList.add('d-none');

    var tr = document.createElement('tr');

    var tdPlaca = document.createElement('td');
    tdPlaca.textContent = placa;
    tr.appendChild(tdPlaca);

    var tdStatus = document.createElement('td');
    var badge = document.createElement('span');
    if (status === 'REGULAR') {
        badge.className = 'badge bg-success';
        badge.textContent = 'REGULAR';
    } else {
        badge.className = 'badge bg-danger';
        badge.textContent = 'IRREGULAR';
    }
    tdStatus.appendChild(badge);
    tr.appendChild(tdStatus);

    var tdHora = document.createElement('td');
    tdHora.textContent = new Date().toLocaleTimeString('pt-BR');
    tr.appendChild(tdHora);

    // Insere no topo da tabela
    tbody.insertBefore(tr, tbody.firstChild);
}
