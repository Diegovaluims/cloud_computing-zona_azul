# Zona Azul - Sistema de Estacionamento Digital (Cloud-Native)

Um laboratório prático focado em **Computação em Nuvem** e **Infraestrutura**, implementando um sistema de controle de estacionamento rotativo (Zona Azul) utilizando uma arquitetura de microsserviços.

## Contexto Acadêmico

Este projeto foi desenvolvido como laboratório de Cloud Computing bem como roteiro de estudos acerca de Infraestruturas em Nuvem, Redes, APIs, Banco de Dados, Docker (o que eu mais queria mexer kkk) e futuramente Terraform. O foco arquitetural (por enquanto) não é a regra de negócio, mas sim a aplicação de conceitos de engenharia de software distribuído, tais como:
* **Conteinerização** e Orquestração Local.
* **Microsserviços** desacoplados.
* **Resiliência** e tratamento de falhas em conexões com Banco de Dados.
* **Preparação para a Nuvem** (Futura implantação e provisionamento via Terraform).

## Arquitetura do Sistema

O sistema foi dividido em três contêineres principais:

1. Banco de Dados único relacional
2. API do Usuário: microsserviço responsável pelo cadastro de clientes, veículos e emissão de reservas de estacionamento.
3. API do Fiscal: microsserviço enxuto de validação assíncrona. Consulta diretamente o banco para verificar o status de uma placa em tempo real.

Ambas as APIs foram desenvolvidas em Python utilizando o framework FastAPI, e compartilham um módulo para gerenciamento de pool de conexões.

## Tecnologias Utilizadas

* **Backend:** Python, FastAPI, Uvicorn
* **Banco de Dados:** PostgreSQL, psycopg2
* **Infraestrutura:** Docker, Docker Compose
* **Integração:** CORS configurado para futuro acoplamento de Frontend

## Como Executar Localmente

### Pré-requisitos
* [Docker](https://www.docker.com/) instalado.
* [Docker Compose](https://docs.docker.com/compose/) instalado.

### Passo a Passo

1. Clone o repositório:
```bash
git clone [https://github.com/SEU_USUARIO/cloud_computing-zona_azul.git](https://github.com/SEU_USUARIO/cloud_computing-zona_azul.git)
cd cloud_computing-zona_azul
```

2. Construa e inicie a infraestrutura de microsserviços em segundo plano:
```bash
docker-compose up -d --build
```

3. Acesso às APIs:
* Painel do Usuário: [http://localhost:8000/docs](http://localhost:8000/docs)
* Painel do Fiscal: [http://localhost:8001/docs](http://localhost:8001/docs)

---

## Comandos Úteis

* `docker-compose stop`
* `docker-compose down` derruba os conteineres (arg -v para rebuildar o banco (em caso de troca de schema)).

---

## Importante!!
Não se esqueça de excluir os contêineres orfãos depois de terminar de testar

1. Lista todos os contêineres existentes
```bash
docker ps -a
```
2. Deleta o contêiner
```bash
docker rm -f nome_conteiner
```

## Próximos Passos

- [x] Criação do Backend (APIs + Banco).
- [x] Estabelecer arquitetura Docker e comunicação de redes.
- [ ] Criação do Frontend.
- [ ] IaC + AWS.

    
## Estrutura de Diretórios

```text
cloud_computing-zona_azul/
├── docker-compose.yml       # Orquestrador global da infraestrutura
├── db/
│   ├── schema.sql           # Script de inicialização do banco
│   ├── database_connect.py  # Módulo compartilhado de pool de conexões e resiliência
│   └── __init__.py          # Exportador do pacote Python
├── backend_usuario/
│   ├── main.py              # Rotas CRUD do usuário e reservas
│   ├── Dockerfile           # Receita de build do microsserviço
│   └── requirements.txt
└── backend_fiscal/
    ├── main.py              # Rota GET simplificada para validação de placas
    ├── Dockerfile           # Receita de build do microsserviço
    └── requirements.txt
```
