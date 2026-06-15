const formLogin = document.getElementById('formLogin');
const formCadastro = document.getElementById('formCadastro');
const divErro = document.getElementById('mensagemErro');
const divSucesso = document.getElementById('mensagemSucesso');

// API corrigida apontando para a AWS
const API_USUARIO = 'http://54.232.52.178:8000';

// Limpa qualquer ID antigo guardado de testes locais, caso esteja rodando na tela de login
// Mas só faz isso se tiver acabado de abrir a página (sem erro prévio)
if (!sessionStorage.getItem('cleaned')) {
    localStorage.removeItem('id_usuario');
    localStorage.removeItem('nome_usuario');
    sessionStorage.setItem('cleaned', 'true');
}

// Função para alternar entre as telas de Login e Cadastro
function toggleMode(mode) {
    divErro.classList.add('d-none');
    divSucesso.classList.add('d-none');
    if (mode === 'cadastro') {
        document.getElementById('loginSection').classList.remove('active');
        document.getElementById('cadastroSection').classList.add('active');
    } else {
        document.getElementById('cadastroSection').classList.remove('active');
        document.getElementById('loginSection').classList.add('active');
    }
}

// === FLUXO DE LOGIN ===
formLogin.addEventListener('submit', async function (evento) {
    evento.preventDefault();
    const emailDigitado = document.getElementById('emailLogin').value;
    const btn = document.getElementById('btnLogin');
    const spinner = document.getElementById('spinnerLogin');

    // Reset de mensagens e UI state
    divErro.classList.add('d-none');
    btn.disabled = true;
    spinner.classList.remove('d-none');

    try {
        const resposta = await fetch(`${API_USUARIO}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: emailDigitado })
        });

        if (resposta.ok) {
            const dados = await resposta.json();
            // Limpa o Storage para garantir um estado limpo, depois seta o novo
            localStorage.clear();
            localStorage.setItem('id_usuario', dados.id_usuario);
            localStorage.setItem('nome_usuario', dados.nome);
            window.location.href = 'painel_usuario.html';
        } else if (resposta.status === 404) {
            mostrarErro("Usuário não encontrado. Se ainda não possui conta, clique em Cadastre-se.");
        } else {
            mostrarErro("Erro no servidor ao tentar realizar login.");
        }
    } catch (erro) {
        console.error(erro);
        mostrarErro("Falha de conexão com a API. Verifique sua internet ou se o servidor AWS está rodando.");
    } finally {
        btn.disabled = false;
        spinner.classList.add('d-none');
    }
});

// === FLUXO DE CADASTRO ===
formCadastro.addEventListener('submit', async function (evento) {
    evento.preventDefault();
    const nomeDigitado = document.getElementById('nomeCadastro').value;
    const emailDigitado = document.getElementById('emailCadastro').value;
    const btn = document.getElementById('btnCadastro');
    const spinner = document.getElementById('spinnerCadastro');

    // Reset de mensagens e UI state
    divErro.classList.add('d-none');
    divSucesso.classList.add('d-none');
    btn.disabled = true;
    spinner.classList.remove('d-none');

    try {
        const resposta = await fetch(`${API_USUARIO}/usuarios`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome: nomeDigitado, email: emailDigitado })
        });

        if (resposta.ok) {
            const dados = await resposta.json();
            mostrarSucesso("Conta criada com sucesso! Redirecionando...");

            // Limpa o Storage para garantir um estado limpo, depois seta o novo
            localStorage.clear();
            localStorage.setItem('id_usuario', dados.id_usuario);
            localStorage.setItem('nome_usuario', nomeDigitado);

            setTimeout(() => {
                window.location.href = 'painel_usuario.html';
            }, 1500);

        } else if (resposta.status === 409) {
            mostrarErro("Este e-mail já está cadastrado no sistema.");
        } else {
            mostrarErro("Erro ao criar usuário. Verifique os dados.");
        }
    } catch (erro) {
        console.error(erro);
        mostrarErro("Falha de conexão com a API ao tentar criar a conta.");
    } finally {
        btn.disabled = false;
        spinner.classList.add('d-none');
    }
});

// Funções auxiliares para feedback visual
function mostrarErro(mensagem) {
    divErro.textContent = mensagem;
    divErro.classList.remove('d-none');
    divSucesso.classList.add('d-none');
}

function mostrarSucesso(mensagem) {
    divSucesso.textContent = mensagem;
    divSucesso.classList.remove('d-none');
    divErro.classList.add('d-none');
}