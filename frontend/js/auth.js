// 1. Mapeando os elementos da tela
const form = document.getElementById('formLogin');
const inputEmail = document.getElementById('email');
const divErro = document.getElementById('mensagemErro');

// 2. Interceptando o momento em que o usuário tenta logar
form.addEventListener('submit', async function (evento) {
    // Evita que a página recarregue (comportamento padrão do HTML)
    evento.preventDefault();

    const emailDigitado = inputEmail.value;

    try {
        // 3. Batendo na porta da sua API do Usuário
        // OBS: Você precisará ter uma rota POST /login no seu main.py
        const resposta = await fetch('http://localhost:8000/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email: emailDigitado })
        });

        // 4. Verificando se a API respondeu com sucesso (Status 200 OK)
        if (resposta.ok) {
            const dados = await resposta.json();

            // 5. A simulação do Login: Salvando os dados na memória do navegador
            localStorage.setItem('id_usuario', dados.id_usuario);
            localStorage.setItem('nome_usuario', dados.nome);

            // Redireciona o usuário para o painel principal (que criaremos depois)
            window.location.href = 'painel_usuario.html';

        } else {
            // Se a API retornar erro (ex: e-mail não existe no banco)
            mostrarErro("Usuário não encontrado. Verifique o e-mail digitado.");
        }
    } catch (erro) {
        // Se a API estiver desligada ou houver bloqueio de CORS
        console.error(erro);
        mostrarErro("Falha ao conectar com o servidor. A API está rodando?");
    }
});

// Função auxiliar para exibir a mensagem vermelha de erro
function mostrarErro(mensagem) {
    divErro.textContent = mensagem;
    divErro.classList.remove('d-none'); // Remove a classe que esconde o elemento
}