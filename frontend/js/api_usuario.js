/**
 * api_usuario.js — Integração do Painel do Usuário com a API (porta 8000)
 *
 * Funções: CRUD de veículos na garagem, emissão e remoção de reservas.
 * Segurança: usa textContent e createElement para inserção no DOM (sem innerHTML).
 */

const API_USUARIO = 'http://localhost:8000';

// --- Sessão ---
const idUsuario = localStorage.getItem('id_usuario');
const nomeUsuario = localStorage.getItem('nome_usuario');

if (!idUsuario) {
    // TODO(security): Implementar autenticação real com tokens HttpOnly em vez de localStorage
    window.location.href = 'index.html';
}

document.getElementById('nomeUsuario').textContent = nomeUsuario;

document.getElementById('btnLogout').addEventListener('click', function () {
    localStorage.removeItem('id_usuario');
    localStorage.removeItem('nome_usuario');
    window.location.href = 'index.html';
});

// --- Utilitários ---
function mostrarAlerta(elementoId, mensagem, tipo) {
    const el = document.getElementById(elementoId);
    el.textContent = mensagem;
    el.className = 'alert alert-' + tipo;
    setTimeout(function () {
        el.className = 'alert d-none';
    }, 3000);
}

// --- GARAGEM: carregar veículos ---
async function carregarVeiculos() {
    try {
        const resp = await fetch(API_USUARIO + '/usuarios/' + idUsuario + '/veiculos');
        const veiculos = await resp.json();

        const tbody = document.getElementById('tabelaVeiculos');
        const select = document.getElementById('selectPlacaReserva');
        const semVeiculos = document.getElementById('semVeiculos');

        // Limpa tabela e select de forma segura
        tbody.replaceChildren();

        // Mantém a primeira option padrão do select
        while (select.options.length > 1) {
            select.remove(1);
        }

        if (veiculos.length === 0) {
            semVeiculos.classList.remove('d-none');
            return;
        }
        semVeiculos.classList.add('d-none');

        veiculos.forEach(function (v) {
            // Linha na tabela
            var tr = document.createElement('tr');

            var tdPlaca = document.createElement('td');
            tdPlaca.textContent = v.placa;
            tr.appendChild(tdPlaca);

            var tdModelo = document.createElement('td');
            tdModelo.textContent = v.modelo;
            tr.appendChild(tdModelo);

            var tdAno = document.createElement('td');
            tdAno.textContent = v.ano;
            tr.appendChild(tdAno);

            var tdAcao = document.createElement('td');
            var btnRemover = document.createElement('button');
            btnRemover.textContent = '✕';
            btnRemover.className = 'btn btn-outline-danger btn-sm';
            btnRemover.addEventListener('click', function () {
                removerVeiculo(v.id_veiculo);
            });
            tdAcao.appendChild(btnRemover);
            tr.appendChild(tdAcao);

            tbody.appendChild(tr);

            // Option no select de reserva
            var opt = document.createElement('option');
            opt.value = v.placa;
            opt.textContent = v.placa + ' — ' + v.modelo;
            select.appendChild(opt);
        });
    } catch (err) {
        mostrarAlerta('alertGaragem', 'Erro ao carregar veículos.', 'danger');
    }
}

// --- GARAGEM: adicionar veículo ---
document.getElementById('formVeiculo').addEventListener('submit', async function (e) {
    e.preventDefault();

    var placa = document.getElementById('inputPlaca').value.trim();
    var modelo = document.getElementById('inputModelo').value.trim();
    var ano = parseInt(document.getElementById('inputAno').value, 10);

    try {
        var resp = await fetch(API_USUARIO + '/usuarios/' + idUsuario + '/veiculos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ placa: placa, modelo: modelo, ano: ano })
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
        mostrarAlerta('alertGaragem', 'Erro de conexão com a API.', 'danger');
    }
});

// --- GARAGEM: remover veículo ---
async function removerVeiculo(idVeiculo) {
    try {
        var resp = await fetch(API_USUARIO + '/veiculos/' + idVeiculo, {
            method: 'DELETE'
        });

        if (resp.ok) {
            mostrarAlerta('alertGaragem', 'Veículo removido!', 'success');
            carregarVeiculos();
            carregarReservas();
        } else {
            var erro = await resp.json();
            mostrarAlerta('alertGaragem', erro.detail || 'Erro ao remover.', 'danger');
        }
    } catch (err) {
        mostrarAlerta('alertGaragem', 'Erro de conexão com a API.', 'danger');
    }
}

// --- RESERVAS: carregar ---
async function carregarReservas() {
    try {
        var resp = await fetch(API_USUARIO + '/reservas');
        var todasReservas = await resp.json();
        var reservas = todasReservas.filter(function (r) {
            return r.id_usuario === parseInt(idUsuario, 10);
        });

        var tbody = document.getElementById('tabelaReservas');
        var semReservas = document.getElementById('semReservas');

        tbody.replaceChildren();

        if (reservas.length === 0) {
            semReservas.classList.remove('d-none');
            return;
        }
        semReservas.classList.add('d-none');

        reservas.forEach(function (r) {
            var tr = document.createElement('tr');

            var tdId = document.createElement('td');
            tdId.textContent = r.id_reserva;
            tr.appendChild(tdId);

            var tdVeiculo = document.createElement('td');
            tdVeiculo.textContent = 'Veículo #' + r.id_veiculo;
            tr.appendChild(tdVeiculo);

            var tdAcao = document.createElement('td');
            var btnCancelar = document.createElement('button');
            btnCancelar.textContent = 'Cancelar';
            btnCancelar.className = 'btn btn-outline-danger btn-sm';
            btnCancelar.addEventListener('click', function () {
                cancelarReserva(r.id_reserva);
            });
            tdAcao.appendChild(btnCancelar);
            tr.appendChild(tdAcao);

            tbody.appendChild(tr);
        });
    } catch (err) {
        mostrarAlerta('alertReserva', 'Erro ao carregar reservas.', 'danger');
    }
}

// --- RESERVAS: emitir ---
document.getElementById('formReserva').addEventListener('submit', async function (e) {
    e.preventDefault();

    var placa = document.getElementById('selectPlacaReserva').value;

    if (!placa) {
        mostrarAlerta('alertReserva', 'Selecione um veículo.', 'warning');
        return;
    }

    try {
        var resp = await fetch(API_USUARIO + '/reservas', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id_usuario: parseInt(idUsuario, 10), placa: placa })
        });

        if (resp.ok) {
            mostrarAlerta('alertReserva', 'Reserva efetuada!', 'success');
            carregarReservas();
        } else {
            var erro = await resp.json();
            mostrarAlerta('alertReserva', erro.detail || 'Erro ao reservar.', 'danger');
        }
    } catch (err) {
        mostrarAlerta('alertReserva', 'Erro de conexão com a API.', 'danger');
    }
});

// --- RESERVAS: cancelar ---
async function cancelarReserva(idReserva) {
    try {
        var resp = await fetch(API_USUARIO + '/reservas/' + idReserva, {
            method: 'DELETE'
        });

        if (resp.ok) {
            mostrarAlerta('alertReserva', 'Reserva cancelada!', 'success');
            carregarReservas();
        } else {
            var erro = await resp.json();
            mostrarAlerta('alertReserva', erro.detail || 'Erro ao cancelar.', 'danger');
        }
    } catch (err) {
        mostrarAlerta('alertReserva', 'Erro de conexão com a API.', 'danger');
    }
}

// --- Inicialização ---
carregarVeiculos();
carregarReservas();
