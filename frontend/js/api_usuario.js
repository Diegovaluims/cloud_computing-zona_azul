/**
 * api_usuario.js — SPA Logic para o Painel do Usuário (MVP v2)
 */

const API_USUARIO = '/api/usuario';
const API_AUTH = '/api/auth';

// --- Sessão ---
const idUsuario = localStorage.getItem('id_usuario');
const nomeUsuario = localStorage.getItem('nome_usuario');

if (!idUsuario) {
    window.location.href = 'index.html';
}

// Update UI
document.getElementById('nomeUsuarioSidebar').textContent = nomeUsuario;
document.getElementById('nomeUsuarioDash').textContent = nomeUsuario;

document.getElementById('btnLogout').addEventListener('click', async function () {
    try {
        await fetch(API_AUTH + '/logout', { method: 'POST', credentials: 'include' });
    } catch(e) {}
    localStorage.removeItem('id_usuario');
    localStorage.removeItem('nome_usuario');
    window.location.href = 'index.html';
});

// --- SPA Navigation ---
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', function() {
        // Remover active de todos os itens e seções
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        document.querySelectorAll('.secao-spa').forEach(s => s.classList.remove('active'));
        
        // Adicionar active no item clicado e na seção correspondente
        this.classList.add('active');
        const targetId = this.getAttribute('data-target');
        document.getElementById(targetId).classList.add('active');

        // Refresh de dados específicos da aba
        if (targetId === 'secao-dashboard') carregarDashboard();
        if (targetId === 'secao-garagem') carregarVeiculos();
        if (targetId === 'secao-reservas') carregarReservas();
        if (targetId === 'secao-carteira') carregarCarteira();
        if (targetId === 'secao-multas') carregarMultas();
        if (targetId === 'secao-perfil') carregarPerfil();
    });
});

// --- Utilitários ---
function mostrarAlerta(elementoId, mensagem, tipo) {
    const el = document.getElementById(elementoId);
    el.textContent = mensagem;
    el.className = 'alert-glass alert-' + tipo;
    setTimeout(function () {
        el.className = 'alert-glass d-none';
    }, 4000);
}

// --- DASHBOARD ---
function carregarDashboard() {
    carregarCarteira(true);
}

// --- GARAGEM ---
async function carregarVeiculos() {
    try {
        const resp = await fetch(API_USUARIO + '/usuarios/' + idUsuario + '/veiculos', { credentials: 'include' });
        const veiculos = await resp.json();

        const tbody = document.getElementById('tabelaVeiculos');
        const select = document.getElementById('selectPlacaReserva');
        const semVeiculos = document.getElementById('semVeiculos');

        tbody.replaceChildren();
        while (select.options.length > 1) select.remove(1);

        if (veiculos.length === 0) {
            semVeiculos.classList.remove('d-none');
            return;
        }
        semVeiculos.classList.add('d-none');

        veiculos.forEach(v => {
            var tr = document.createElement('tr');
            tr.innerHTML = `<td>${v.placa}</td><td>${v.modelo}</td><td>${v.ano}</td>`;
            
            var tdAcao = document.createElement('td');
            var btn = document.createElement('button');
            btn.textContent = 'Remover';
            btn.className = 'btn btn-outline-danger btn-sm';
            btn.onclick = () => removerVeiculo(v.id_veiculo);
            tdAcao.appendChild(btn);
            tr.appendChild(tdAcao);
            tbody.appendChild(tr);

            var opt = document.createElement('option');
            opt.value = v.placa;
            opt.textContent = `${v.placa} — ${v.modelo}`;
            select.appendChild(opt);
        });
    } catch (err) {}
}

document.getElementById('formVeiculo').addEventListener('submit', async function (e) {
    e.preventDefault();
    var placa = document.getElementById('inputPlaca').value.trim().toUpperCase();
    var modelo = document.getElementById('inputModelo').value.trim();
    var ano = parseInt(document.getElementById('inputAno').value, 10);

    try {
        var resp = await fetch(API_USUARIO + '/usuarios/' + idUsuario + '/veiculos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ placa, modelo, ano }),
            credentials: 'include'
        });

        if (resp.ok) {
            mostrarAlerta('alertGaragem', 'Veículo adicionado!', 'success');
            document.getElementById('formVeiculo').reset();
            carregarVeiculos();
        } else {
            var erro = await resp.json();
            mostrarAlerta('alertGaragem', erro.detail || 'Erro ao adicionar.', 'danger');
        }
    } catch (err) {
        mostrarAlerta('alertGaragem', 'Erro de conexão.', 'danger');
    }
});

async function removerVeiculo(id) {
    if(!confirm("Tem certeza que deseja remover este veículo? Todas as reservas associadas a ele também serão removidas.")) return;
    try {
        var resp = await fetch(API_USUARIO + '/veiculos/' + id, { method: 'DELETE', credentials: 'include' });
        if (resp.ok) carregarVeiculos();
        else mostrarAlerta('alertGaragem', 'Erro ao remover.', 'danger');
    } catch (err) {}
}

// --- RESERVAS ---
async function carregarReservas() {
    try {
        var resp = await fetch(API_USUARIO + '/reservas', { credentials: 'include' });
        var todasReservas = await resp.json();
        var reservas = todasReservas.filter(r => r.id_usuario === parseInt(idUsuario, 10));

        var tbody = document.getElementById('tabelaReservas');
        var semReservas = document.getElementById('semReservas');

        tbody.replaceChildren();

        if (reservas.length === 0) {
            semReservas.classList.remove('d-none');
            return;
        }
        semReservas.classList.add('d-none');

        reservas.forEach(r => {
            var tr = document.createElement('tr');
            
            // Format date if possible, assuming r.expira_em is returned somehow 
            // Note: Our backend endpoint /reservas might not be returning expira_em in the MVP yet,
            // but let's assume it does or just print what we have
            var statusBadge = r.status === 'ATIVA' ? '<span class="badge bg-success">ATIVA</span>' : '<span class="badge bg-secondary">EXPIRADA</span>';
            
            tr.innerHTML = `<td>${r.id_reserva}</td><td>${r.placa}</td><td>-</td><td>-</td><td>${statusBadge}</td>`;
            
            var tdAcao = document.createElement('td');
            var btn = document.createElement('button');
            btn.textContent = 'Cancelar';
            btn.className = 'btn btn-outline-danger btn-sm';
            btn.onclick = () => cancelarReserva(r.id_reserva);
            tdAcao.appendChild(btn);
            tr.appendChild(tdAcao);

            tbody.appendChild(tr);
        });
    } catch (err) {}
}

document.getElementById('formReserva').addEventListener('submit', async function (e) {
    e.preventDefault();
    var placa = document.getElementById('selectPlacaReserva').value;
    var duracao = parseInt(document.getElementById('inputDuracao').value, 10);

    if (!placa) return mostrarAlerta('alertReserva', 'Selecione um veículo.', 'warning');

    try {
        var resp = await fetch(API_USUARIO + '/reservas', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id_usuario: parseInt(idUsuario, 10), placa: placa, duracao_horas: duracao }),
            credentials: 'include'
        });

        if (resp.ok) {
            mostrarAlerta('alertReserva', 'Reserva efetuada com sucesso!', 'success');
            document.getElementById('formReserva').reset();
            carregarReservas();
            carregarCarteira(); // Atualiza saldo escondido
        } else {
            var erro = await resp.json();
            mostrarAlerta('alertReserva', erro.detail || 'Erro ao reservar.', 'danger');
        }
    } catch (err) {
        mostrarAlerta('alertReserva', 'Erro de conexão.', 'danger');
    }
});

async function cancelarReserva(id) {
    try {
        var resp = await fetch(API_USUARIO + '/reservas/' + id, { method: 'DELETE', credentials: 'include' });
        if (resp.ok) carregarReservas();
    } catch (err) {}
}

// --- CARTEIRA ---
async function carregarCarteira(onlyDash = false) {
    try {
        var resp = await fetch(API_USUARIO + '/carteira', { credentials: 'include' });
        if (resp.ok) {
            var data = await resp.json();
            document.getElementById('saldoDash').textContent = `R$ ${data.saldo.toFixed(2).replace('.', ',')}`;
            if (onlyDash) return;
            
            document.getElementById('saldoCarteira').textContent = `R$ ${data.saldo.toFixed(2).replace('.', ',')}`;
            
            var tbody = document.getElementById('tabelaTransacoes');
            tbody.replaceChildren();
            data.transacoes.forEach(t => {
                var tr = document.createElement('tr');
                var d = new Date(t.criado_em).toLocaleString();
                var color = t.valor < 0 ? 'text-danger' : 'text-success';
                tr.innerHTML = `<td>${d}</td><td>${t.tipo}</td><td class="fw-bold ${color}">R$ ${t.valor.toFixed(2)}</td>`;
                tbody.appendChild(tr);
            });
        }
    } catch (err) {}
}

document.getElementById('formRecarga').addEventListener('submit', async function(e) {
    e.preventDefault();
    var valor = parseFloat(document.getElementById('inputRecarga').value);
    try {
        var resp = await fetch(API_USUARIO + '/carteira/recarga', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ valor }),
            credentials: 'include'
        });
        if (resp.ok) {
            mostrarAlerta('alertCarteira', 'Recarga simulada com sucesso!', 'success');
            document.getElementById('inputRecarga').value = '10.00';
            carregarCarteira();
        } else {
            mostrarAlerta('alertCarteira', 'Erro na recarga.', 'danger');
        }
    } catch (err) {}
});

// --- PERFIL ---
async function carregarPerfil() {
    try {
        var resp = await fetch(API_USUARIO + '/perfil', { credentials: 'include' });
        if (resp.ok) {
            var data = await resp.json();
            document.getElementById('inputPerfilNome').value = data.nome;
            document.getElementById('inputPerfilEmail').value = data.email;
        }
    } catch (err) {}
}

document.getElementById('formPerfil').addEventListener('submit', async function(e) {
    e.preventDefault();
    var nome = document.getElementById('inputPerfilNome').value;
    var email = document.getElementById('inputPerfilEmail').value;
    try {
        var resp = await fetch(API_USUARIO + '/perfil', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome, email }),
            credentials: 'include'
        });
        if (resp.ok) {
            mostrarAlerta('alertPerfil', 'Perfil atualizado!', 'success');
            localStorage.setItem('nome_usuario', nome);
            document.getElementById('nomeUsuarioSidebar').textContent = nome;
            document.getElementById('nomeUsuarioDash').textContent = nome;
        } else {
            mostrarAlerta('alertPerfil', 'Erro ao atualizar perfil.', 'danger');
        }
    } catch (err) {}
});

document.getElementById('formSenha').addEventListener('submit', async function(e) {
    e.preventDefault();
    var atual = document.getElementById('inputSenhaAtual').value;
    var nova = document.getElementById('inputNovaSenha').value;
    try {
        var resp = await fetch(API_USUARIO + '/perfil/senha', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ senha_atual: atual, nova_senha: nova }),
            credentials: 'include'
        });
        if (resp.ok) {
            mostrarAlerta('alertSenha', 'Senha alterada com sucesso!', 'success');
            document.getElementById('formSenha').reset();
        } else {
            var erro = await resp.json();
            mostrarAlerta('alertSenha', erro.detail || 'Erro ao alterar.', 'danger');
        }
    } catch (err) {}
});

// --- MULTAS ---
async function carregarMultas() {
    try {
        var resp = await fetch(API_USUARIO + '/multas', { credentials: 'include' });
        if (resp.ok) {
            var multas = await resp.json();
            var tbody = document.getElementById('tabelaMultas');
            var semMultas = document.getElementById('semMultas');

            tbody.replaceChildren();
            if (multas.length === 0) {
                semMultas.classList.remove('d-none');
                return;
            }
            semMultas.classList.add('d-none');

            multas.forEach(m => {
                var tr = document.createElement('tr');
                var d = new Date(m.criado_em).toLocaleDateString();
                var statusBadge = m.status === 'PAGA' ? '<span class="badge bg-success">PAGA</span>' : '<span class="badge bg-danger">PENDENTE</span>';
                
                tr.innerHTML = `<td>${d}</td><td>${m.placa}</td><td>${m.motivo}</td><td>R$ ${m.valor.toFixed(2)}</td><td>${statusBadge}</td>`;
                
                var tdAcao = document.createElement('td');
                if (m.status !== 'PAGA') {
                    var btn = document.createElement('button');
                    btn.textContent = 'Pagar com Saldo';
                    btn.className = 'btn btn-outline-success btn-sm';
                    btn.onclick = () => pagarMulta(m.id_multa);
                    tdAcao.appendChild(btn);
                }
                tr.appendChild(tdAcao);
                tbody.appendChild(tr);
            });
        }
    } catch (err) {}
}

async function pagarMulta(id) {
    try {
        var resp = await fetch(API_USUARIO + `/multas/${id}/pagar`, { method: 'POST', credentials: 'include' });
        if (resp.ok) {
            mostrarAlerta('alertMultas', 'Multa paga com sucesso!', 'success');
            carregarMultas();
            carregarCarteira();
        } else {
            var erro = await resp.json();
            mostrarAlerta('alertMultas', erro.detail || 'Erro ao pagar multa.', 'danger');
        }
    } catch (err) {}
}

// Init
carregarDashboard();
carregarVeiculos();
